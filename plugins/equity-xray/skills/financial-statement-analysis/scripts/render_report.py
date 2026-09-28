#!/usr/bin/env python3
"""Render an offline HTML research document with sourced SVG charts (stdlib only)."""
import argparse
import base64
import html
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

COLORS = ['#183a56', '#168b8c', '#d68b39', '#788897', '#9b6b9e']
SECTION_IDS = ['roe', 'revenue', 'gross_margin', 'profit', 'turnover', 'leverage', 'cash_flow', 'anomalies', 'business_strategy']
E = lambda x: html.escape(str(x), quote=True)


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def fmt(x):
    if x is None:
        return '数据不足'
    if not finite(x):
        return str(x)
    return f'{x:,.2f}'.rstrip('0').rstrip('.')


class Renderer:
    def __init__(self, report, base):
        self.report, self.base = report, base
        wp = json.loads((base / report['workpapers']).read_text(encoding='utf-8'))
        self.nodes = {n['id']: n for group in ['raw', 'metrics'] for n in wp[group]}
        self.sources = {s['id']: s for s in wp['sources']}
        self.wp = wp
        if any(c['status']=='FAIL' for c in wp['checks']) and not report.get('unresolved_check_explanation'):
            raise ValueError('Unresolved data checks: fix inputs or explicitly explain the draft limitation')
        for n in report.get('extra_data', []):
            if n['id'] in self.nodes or not n.get('formula') or not n.get('source_ids') or not n.get('dependencies'):
                raise ValueError('Extra data needs unique id, formula, dependencies and source_ids')
            if n['value'] is not None and not finite(n['value']):
                raise ValueError('Invalid extra data value')
            if not set(n['source_ids']).issubset(self.sources):
                raise ValueError('Unknown extra source')
            if not set(n['dependencies']).issubset(self.nodes):
                raise ValueError('Extra data dependencies must exist earlier')
            self.nodes[n['id']] = n

    def value(self, ref, scale=1):
        if ref not in self.nodes:
            raise ValueError('Unknown data reference: ' + str(ref))
        if not finite(scale):
            raise ValueError('Scale must be finite')
        x = self.nodes[ref]['value']
        return x * scale if x is not None else None

    def citations(self, refs=(), sources=()):
        ids = set(sources)
        for ref in refs:
            if ref not in self.nodes:
                raise ValueError('Unknown evidence reference: ' + str(ref))
            ids.update(self.nodes[ref].get('source_ids', []))
        if not ids.issubset(self.sources):
            raise ValueError('Unknown citation')
        return ' '.join(f'<a class="cite" href="#src-{E(s)}">[{E(s)}]</a>' for s in sorted(ids))

    def statement(self, obj):
        if not isinstance(obj, dict) or not obj.get('text'):
            raise ValueError('Research statements must be objects with text, kind and evidence')
        if obj.get('kind') not in ['财务事实', '管理层解释', '公司管理层解释', '外部证据', '分析推断', '研究问题', '数据限制']:
            raise ValueError('Invalid statement kind')
        if obj['kind'] in ['财务事实', '管理层解释', '公司管理层解释', '外部证据', '分析推断'] and not (obj.get('refs') or obj.get('source_ids')):
            raise ValueError('Financial/management/inference statements need evidence')
        return f'<span class="kind">【{E(obj["kind"])}】</span>{E(obj["text"])} {self.citations(obj.get("refs", []), obj.get("source_ids", []))}'

    def list_statements(self, rows):
        return '<ul>' + ''.join('<li>' + self.statement(x) + '</li>' for x in rows) + '</ul>'

    def table(self, columns, rows):
        return '<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th>{E(c)}</th>' for c in columns) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{E(fmt(v))}</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table></div>'

    def chart(self, spec):
        for key in ['title', 'conclusion', 'how_to_read', 'findings', 'interpretation', 'drilldown']:
            if not spec.get(key):
                raise ValueError('Chart missing ' + key)
        refs = []
        if spec.get('image_path'):
            refs = spec.get('data_refs', [])
            if not refs:
                raise ValueError('External charts require data_refs')
            path = (self.base / spec['image_path']).resolve()
            mime = {'.svg': 'image/svg+xml', '.png': 'image/png'}.get(path.suffix.lower())
            if not mime:
                raise ValueError('Use SVG or PNG')
            if path.suffix.lower() == '.svg':
                source = path.read_text(encoding='utf-8').lower()
                if any(t in source for t in ['<script', '<foreignobject', 'javascript:']) or re.search(r'(?:href|src)\s*=\s*[\"\'](?:https?:|//|file:)',source) or re.search(r'\son[a-z]+\s*=',source):
                    raise ValueError('SVG contains active or external elements')
            data_uri = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()
            visual = f'<img class="chart" src="{data_uri}" alt="{E(spec["title"])}">'
            rows = [[r, self.value(r), self.nodes[r].get('unit', '')] for r in refs]
            table = self.table(['数据ID', '数值', '单位'], rows)
        else:
            visual, table, refs = self.svg(spec)
        drill = spec['drilldown']
        if drill.get('needed') not in [True, False] or not drill.get('next'):
            raise ValueError('drilldown needs boolean needed and next/reason')
        return f'<figure><h3>{E(spec["title"])}</h3>{visual}<figcaption><p class="chart-conclusion"><strong>图表结论：</strong>{self.statement(spec["conclusion"])}</p><p><strong>【怎么看】</strong>{E(spec["how_to_read"])}</p><div><strong>【发现／数据事实】</strong>{self.list_statements(spec["findings"])}</div><p><strong>【解读／分析】</strong>{self.statement(spec["interpretation"])}</p><p><strong>【是否需要继续拆解】</strong>{"是" if drill["needed"] else "否"}；{E(drill["next"])}</p><p class="source">图表来源：{self.citations(refs)}</p></figcaption><details><summary>图表数据与引用</summary>{table}</details></figure>'

    def svg(self, spec):
        kind = spec['type']
        width, height, left, right, top, bottom = 960, 430, 95, 35, 54, 92
        legend_rows = max(1, math.ceil(len(spec.get('series', []))/3))
        top += 20*(legend_rows-1)
        pw, ph = width-left-right, height-top-bottom
        refs, rows, shapes = [], [], []
        def text(x, y, value, anchor='start', color='#425366', size=14):
            return f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" fill="{color}" font-size="{size}">{E(value)}</text>'
        def line(x1,y1,x2,y2,color='#dfe5ea',dash=''):
            return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-dasharray="{dash}"/>'
        def rect(x,y,w,h,color):
            return f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(w,0):.2f}" height="{max(h,0):.2f}" fill="{color}"/>'
        if kind == 'scatter':
            xs, ys, points = [], [], []
            for p in spec['points']:
                xr, yr = p['x_ref'], p['y_ref']
                refs += [xr, yr]
                x, y = self.value(xr, spec.get('x_scale',1)), self.value(yr,spec.get('y_scale',1))
                rows.append([p['label'],x,y,xr,yr])
                if x is not None and y is not None:
                    xs.append(x); ys.append(y); points.append((p['label'],x,y))
            if not points:
                raise ValueError('No available scatter points')
            xmin, xmax = min(0,min(xs)), max(0,max(xs))
            xmax = xmax if xmax != xmin else xmin+1
            ymin, ymax = min(0,min(ys)), max(0,max(ys))
            ymax = ymax if ymax != ymin else ymin+1
            xmap = lambda x: left+(x-xmin)/(xmax-xmin)*pw
            ymap = lambda y: top+ph-(y-ymin)/(ymax-ymin)*ph
            for i in range(6):
                x=xmin+(xmax-xmin)*i/5; y=ymin+(ymax-ymin)*i/5
                shapes += [line(left,ymap(y),left+pw,ymap(y)),text(left-12,ymap(y)+5,fmt(y),'end'),text(xmap(x),top+ph+24,fmt(x),'middle')]
            for label,x,y in points:
                shapes += [f'<circle cx="{xmap(x):.2f}" cy="{ymap(y):.2f}" r="7" fill="{COLORS[0]}"><title>{E(label)}: {E(fmt(x))}, {E(fmt(y))}</title></circle>',text(xmap(x)-8 if xmap(x)>left+pw-110 else xmap(x)+8,ymap(y)-10,label,'end' if xmap(x)>left+pw-110 else 'start')]
            shapes += [text(left,25,spec['y_label']),text(left+pw/2,height-18,spec['x_label'],'middle')]
            headers=['公司',spec['x_label'],spec['y_label'],'X引用','Y引用']
        else:
            labels=spec.get('labels',[])
            if kind=='waterfall':
                labels=[s['label'] for s in spec['steps']]
                current=0; bars=[]; allv=[0]
                for index, step in enumerate(spec['steps']):
                    ref=step['ref']; refs.append(ref)
                    value=self.value(ref,step.get('scale',1))
                    if value is None:
                        raise ValueError('Waterfall requires complete values; use another chart')
                    if step['kind']=='total':
                        if index > 0 and not math.isclose(current,value,rel_tol=1e-8,abs_tol=spec.get('rounding_tolerance',0.01)):
                            raise ValueError('Waterfall does not reconcile at '+step['label'])
                        a,b=0,value; current=value; color=COLORS[0]
                    elif step['kind']=='delta':
                        a,b=current,current+value; current=b; color=COLORS[1] if value>=0 else '#be5c48'
                    else:
                        raise ValueError('Unknown waterfall step kind')
                    bars.append((a,b,color,value));allv.extend([a,b]);rows.append([step['label'],value,ref])
                series=[]; headers=['项目',spec['unit'],'引用']
            elif kind in ['line','bar','stacked']:
                series=[];allv=[0]
                for s in spec['series']:
                    if len(s['refs'])!=len(labels):
                        raise ValueError('Series/label length mismatch')
                    values=[self.value(ref,s.get('scale',1)) for ref in s['refs']]
                    refs.extend(s['refs']);series.append((s['name'],values))
                    allv.extend(v for v in values if v is not None)
                if not any(v is not None for _,values in series for v in values):
                    raise ValueError('All chart data are missing')
                if kind=='stacked':
                    for i in range(len(labels)):
                        column=[v[i] for _,v in series]
                        if any(x is None for x in column):
                            raise ValueError('Incomplete stack: do not imply missing components are zero')
                        allv.extend([sum(max(v,0) for v in column),sum(min(v,0) for v in column)])
                rows=[[label]+[values[i] for _,values in series] for i,label in enumerate(labels)]
                headers=['期间/对象']+[name+' ('+spec['unit']+')' for name,_ in series]
            else:
                raise ValueError('Unknown chart type: '+kind)
            if not labels:
                raise ValueError('Chart requires labels')
            ymin,ymax=min(allv),max(allv)
            if ymin==ymax: ymax=ymin+1
            rough=(ymax-ymin)/5
            magnitude=10**math.floor(math.log10(rough))
            tick=next(v for v in [1,2,5,10] if v>=rough/magnitude)*magnitude
            ymin=math.floor(ymin/tick)*tick
            ymax=math.ceil(ymax/tick)*tick
            ymap=lambda y:top+ph-(y-ymin)/(ymax-ymin)*ph
            step_width=pw/len(labels)
            xmap=lambda i:left+step_width*(i+0.5)
            for i in range(round((ymax-ymin)/tick)+1):
                val=ymin+tick*i
                shapes += [line(left,ymap(val),left+pw,ymap(val)),text(left-12,ymap(val)+5,fmt(val),'end')]
            shapes += [line(left,ymap(0),left+pw,ymap(0),'#65798b'),text(left,24,spec['unit'])]
            for i,label in enumerate(labels):
                shapes.append(text(xmap(i),top+ph+28,label,'middle',size=12))
            for j,(name,values) in enumerate(series):
                color=COLORS[j%len(COLORS)]
                shapes += [rect(left+(j%3)*pw/3,38+(j//3)*20,12,8,color),text(left+(j%3)*pw/3+17,47+(j//3)*20,name,size=12)]
                previous=None
                for i,value in enumerate(values):
                    if value is None:
                        previous=None
                        if kind=='bar': shapes.append(text(xmap(i),ymap(0)-8,'缺失','middle',size=10))
                        continue
                    x=xmap(i)
                    if kind=='line':
                        y=ymap(value)
                        if previous:
                            shapes.append(line(previous[0],previous[1],x,y,color))
                        shapes.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"><title>{E(name)} {E(labels[i])}: {E(fmt(value))}</title></circle>')
                        previous=(x,y)
                    elif kind=='bar':
                        barw=step_width*0.72/max(len(series),1)
                        xx=x-step_width*.36+j*barw
                        shapes.append(rect(xx,min(ymap(0),ymap(value)),barw*.9,abs(ymap(value)-ymap(0)),color))
            if kind=='stacked':
                for i in range(len(labels)):
                    positive=negative=0
                    for j,(_,values) in enumerate(series):
                        v=values[i]; start=positive if v>=0 else negative; end=start+v
                        if v>=0:positive=end
                        else:negative=end
                        shapes.append(rect(xmap(i)-step_width*.3,min(ymap(start),ymap(end)),step_width*.6,abs(ymap(end)-ymap(start)),COLORS[j%len(COLORS)]))
            if kind=='waterfall':
                for i,(a,b,color,v) in enumerate(bars):
                    shapes += [rect(xmap(i)-step_width*.3,min(ymap(a),ymap(b)),step_width*.6,abs(ymap(b)-ymap(a)),color),text(xmap(i),min(ymap(a),ymap(b))-8,fmt(v),'middle',size=11)]
                    if i<len(bars)-1:
                        shapes.append(line(xmap(i)+step_width*.3,ymap(b),xmap(i+1)-step_width*.3,ymap(b),dash='4 3'))
        svg=f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="{E(spec["title"])}" xmlns="http://www.w3.org/2000/svg"><title>{E(spec["title"])}</title><rect width="100%" height="100%" fill="white"/><g font-family="Microsoft YaHei, PingFang SC, Noto Sans CJK SC, sans-serif">'+''.join(shapes)+'</g></svg>'
        return svg,self.table(headers,rows),refs

    def render(self):
        r=self.report; mode=r['mode']; sections=r['sections'];summary=r['summary']
        if mode not in ['full','quick','deep','compare']:
            raise ValueError('Invalid mode')
        if mode=='full' and [s['id'] for s in sections] != SECTION_IDS:
            raise ValueError('Full report requires nine ordered sections')
        if mode=='quick' and not 5<=sum(len(s.get('charts',[])) for s in sections)<=8:
            raise ValueError('Quick report needs 5–8 charts')
        if mode in ['full','quick'] and not 3<=len(summary['conclusions'])<=5:
            raise ValueError('Summary needs 3–5 conclusions')
        if mode in ['full','quick'] and not 3<=len(summary['questions'])<=5:
            raise ValueError('Summary needs 3–5 questions')
        if not summary.get('anomalies') and not summary.get('anomaly_note'):
            raise ValueError('Record anomalies or an explicit no-evidence/data-gap note')
        indicator_rows=[]
        for row in summary['indicators']:
            value=self.value(row['ref'],row.get('scale',1))
            indicator_rows.append([row['label'],fmt(value)+' '+row['unit'],row['change'],row['explanation']])
        title=f'{r["company"]}｜上市公司财务研究报告'
        body=f'<header><p class="eyebrow">COMPANY FINANCIAL RESEARCH · {E(mode.upper())}</p><h1>{E(title)}</h1><p class="meta">{E(r["ticker"])} · {E(r["period"])} · 数据截止 {E(r["as_of"])} · {E(r["basis"])}</p></header>'
        if r.get('unresolved_check_explanation'):
            body+='<p class="gap">研究初稿：'+E(r['unresolved_check_explanation'])+'</p>'
        body+='<section class="executive" id="executive"><h2>Executive Summary</h2>'+self.list_statements(summary['conclusions'])
        body+='<h3>核心财务指标概览</h3>'+self.table(['指标','最新值','历史变化','核心解释'],indicator_rows)
        body+='<div class="summary-grid"><div><h3>重要财务异常</h3>'+(self.list_statements(summary['anomalies']) if summary.get('anomalies') else '<p>'+E(summary['anomaly_note'])+'</p>')+'</div><div><h3>下一步研究问题</h3><ol>'+''.join('<li>'+E(q)+'</li>' for q in summary['questions'])+'</ol></div></div></section>'
        body+='<nav><strong>正文目录</strong> '+ ' · '.join(f'<a href="#{E(s["id"])}">{E(s["title"])}</a>' for s in sections)+' · <a href="#questions">待验证问题</a> · <a href="#appendix">数据附录</a></nav>'
        for s in sections:
            body+=f'<section class="analysis-section" id="{E(s["id"])}"><h2>{E(s["title"])}</h2><div class="core"><strong>【核心结论】</strong>{self.list_statements(s["conclusions"])}</div>'
            if not s.get('charts') and not s.get('data_gap'):
                raise ValueError('Each section needs a chart or explicit data gap')
            for c in s.get('charts',[]):body+=self.chart(c)
            if s.get('data_gap'):body+='<p class="gap">数据不足：'+E(s['data_gap'])+'</p>'
            status=s['status']
            if status not in ['正常','值得关注','需重点拆解','数据不足']:
                raise ValueError('Invalid status')
            body+='<p><strong>【是否异常】</strong>'+E(status)+'；'+E(s['status_reason'])+'</p>'
            if s.get('drilldown'):
                body+='<h3>【进一步拆解】</h3>'+self.list_statements(s['drilldown'])
            body+='</section>'
        body+='<section id="questions"><h2>10. 待验证问题</h2><ol>'+''.join('<li>'+E(q)+'</li>' for q in r['questions'])+'</ol></section>'
        body+='<section id="appendix"><h2>数据附录</h2>'
        for table in r['appendix_tables']:
            body+='<h3>'+E(table['title'])+'</h3>'+self.table(table['columns'],table['rows'])
        body+='<h3>数据来源</h3><ol class="sources">'
        for sid,s in self.sources.items():
            loc=s['locator'];url=urlparse(loc)
            locator=f'<a href="{E(loc)}">原始来源</a>' if url.scheme in ['http','https'] else E(loc)
            body+=f'<li id="src-{E(sid)}"><strong>{E(sid)} · {E(s["title"])}</strong> — {locator}；披露 {E(s["published_date"])}；获取 {E(s["accessed_date"])}</li>'
        body+='</ol><h3>计算与覆盖检查</h3>'+self.table(['期间','检查','结果','差额'],[[c['record_id'],c['check'],c['status'],c['difference']] for c in self.wp['checks']])+'</section>'
        css=(Path(__file__).resolve().parent.parent/'assets'/'report.css').read_text(encoding='utf-8')
        return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{E(title)}</title><style>{css}</style></head><body><main>{body}</main></body></html>'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('--out',required=True);a=p.parse_args()
    path=Path(a.input).resolve();r=Renderer(json.loads(path.read_text(encoding='utf-8')),path.parent)
    output=r.render();dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(output,encoding='utf-8')
    print(json.dumps({'html':str(dest),'bytes':len(output.encode()),'sources':len(r.sources)},ensure_ascii=False))


if __name__=='__main__':main()
