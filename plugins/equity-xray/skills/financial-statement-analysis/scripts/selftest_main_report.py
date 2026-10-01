#!/usr/bin/env python3
"""Synthetic integration checks for the initial-report contract; no real-company evidence."""
import copy
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from selftest import fixture
from calculate_financial_ratios import analyze
from assess_adjusted_roe import assess
from render_report import Renderer, SECTION_IDS


def dataset(years=range(2021,2026)):
    d=fixture(); base=d['records'][0]; d['records']=[]
    for ticker, adj in [('TARGET',7),('P1',4),('P2',7),('P3',10)]:
        for year in years:
            r=copy.deepcopy(base);r.update(id=f'{ticker}_{year}',ticker=ticker,company='完全虚构_'+ticker,
                period_start=f'{year}-01-01',period_end=f'{year}-12-31',
                adjusted_profit_basis='disclosed_nonrecurring',adjustment_policy_id='synthetic_common_policy_v1')
            v=r['values']
            for field,value in dict(total_assets_open=100,total_assets_close=100,total_equity_open=50,total_equity_close=50,
                total_liabilities_close=50,parent_equity_open=40,parent_equity_close=40,ar_open=15,ar_close=15,
                inventory_open=15,inventory_close=15,trade_payables_open=12,trade_payables_close=12,
                cash_equiv_open=30,cash_equiv_close=30,cfo=15,cfi=-7,cff=-8,available_cash_close=90,
                adjusted_parent_profit=adj,sales_cash_received=110).items():
                v[field]=dict(value=value,source_ids=['SIM'],locator='明确虚构模拟表',original_label=field)
            if year>years[0]:r['prior_record_id']=f'{ticker}_{year-1}'
            d['records'].append(r)
    return d


def run():
    data=dataset(); wp=analyze(data); nodes={n['id']:n for g in ['raw','metrics'] for n in wp[g]}
    value=lambda k:nodes['TARGET_2025:metric:'+k]['value']
    assert not [c for c in wp['checks'] if c['status']=='FAIL']
    assert math.isclose(value('roe_adjusted_parent'),7/40)
    assert math.isclose(value('dupont_adjusted_parent'),7/40)
    assert math.isclose(value('sales_cash_ratio'),1.1)
    assert math.isclose(value('net_profit_cash_content'),1.5)
    assert math.isclose(value('adjusted_profit_share'),7/8)
    assert math.isclose(value('cash_equiv_to_interest_debt'),1.5) # Broad cash 90 is not used.
    score=assess(wp,'TARGET',['P1','P2','P3'])
    assert score['score']==50 and score['stability']['positive_years']==5
    assert score['stability']['std_pp']==0
    future=assess(wp,'TARGET',['P1','P2','P3'],years=[2022,2023,2024,2025,2026])
    assert future['score'] is None and future['missing_years']==[2026]
    assert future['component_status']['stability']=='partial'
    assert '完整覆盖' not in future['stability']['coverage_note']
    peerfail=copy.deepcopy(wp);peerfail['checks'].append(dict(status='FAIL',record_id='P1_2025'))
    rejected_peer=assess(peerfail,'TARGET',['P1','P2','P3'])
    assert rejected_peer['score'] is None and rejected_peer['stability']['years']==5
    unrelated=copy.deepcopy(wp);unrelated['checks'].append(dict(status='FAIL',record_id='OTHER_COMPANY'))
    assert assess(unrelated,'TARGET',['P1','P2','P3'])['score']==50
    missing_year=assess(wp,'TARGET',['P1','P2','P3'],years=[2020,2021,2022,2023])
    assert missing_year['score'] is None
    badbasis=copy.deepcopy(data);badbasis['records'][0]['adjusted_profit_basis']='typo'
    try:analyze(badbasis)
    except ValueError:pass
    else:raise AssertionError('Invalid adjusted-profit basis accepted')
    badbasis=copy.deepcopy(data);badbasis['records'][0]['adjustment_policy_id']=''
    try:analyze(badbasis)
    except ValueError:pass
    else:raise AssertionError('Verified adjusted profit without policy accepted')
    fail=copy.deepcopy(wp);fail['checks'].append(dict(status='FAIL',check='synthetic_failure'))
    rejected=assess(fail,'TARGET',['P1','P2','P3'])
    assert rejected['score'] is None and rejected['stability'] is None
    assert all(row['score'] is None for row in rejected['annual'])
    assert assess(wp,'TARGET',['P1','P2'])['score'] is None
    bad=copy.deepcopy(data);bad['records'][0]['adjusted_profit_basis']='non_gaap'
    bwp=analyze(bad)
    assert next(m['value'] for m in bwp['metrics'] if m['id']=='TARGET_2021:metric:roe_adjusted_parent') is None
    assert assess(bwp,'TARGET',['P1','P2','P3'])['score'] is None
    bad=copy.deepcopy(data);bad['records'][0]['adjustment_policy_id']='different'
    assert assess(analyze(bad),'TARGET',['P1','P2','P3'])['score'] is None
    assert assess(analyze(bad),'TARGET',['P1','P2','P3'])['stability']['years'] == 4
    assert assess(wp,'TARGET',['P1','P2','P3'],years=[2024,2025])['stability'] is None
    short=copy.deepcopy(wp);short['records'][0]['period_start']='2021-07-01'
    assert assess(short,'TARGET',['P1','P2','P3'])['stability']['years']==4
    for field,newvalue,metric in [('net_profit',0,'net_profit_cash_content'),('interest_debt_close',0,'cash_equiv_to_interest_debt'),('parent_equity_open',-1,'roe_adjusted_parent')]:
        d=copy.deepcopy(data);d['records'][0]['values'][field]['value']=newvalue
        out=analyze(d)
        assert next(m['value'] for m in out['metrics'] if m['id']=='TARGET_2021:metric:'+metric) is None
    d=copy.deepcopy(data);del d['records'][0]['values']['sales_cash_received']
    assert next(m['value'] for m in analyze(d)['metrics'] if m['id']=='TARGET_2021:metric:sales_cash_ratio') is None
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp);(path/'analysis.json').write_text(json.dumps(wp));(path/'assessment.json').write_text(json.dumps(score))
        ids=[f'TARGET_{year}' for year in range(2021,2026)]
        fact=lambda text:dict(text=text,kind='财务事实',refs=['TARGET_2025:metric:roe_adjusted_parent'])
        chart=dict(type='line',title='模拟数据：扣非ROE保持不变',unit='%',labels=list(range(2021,2026)),
            series=[dict(name='扣非ROE',refs=[i+':metric:roe_adjusted_parent' for i in ids],scale=100)],
            conclusion=fact('明确虚构，仅验证渲染'),how_to_read='按年查看模拟数据',findings=[fact('模拟数值稳定')],
            interpretation=fact('模拟数据不能用于研究'),drilldown=dict(needed=False,next='模拟验证结束'))
        coverage={}
        fields={'roe_adjusted':'metric:roe_adjusted_parent','revenue':'raw:revenue','cfo':'raw:cfo','capex_cash':'raw:capex_cash','industry_turnover':'metric:inventory_turnover'}
        for key in ['roe_adjusted','revenue','sales_cash_ratio','gross_margin','net_margin','net_profit_cash_content','adjusted_profit_share','asset_turnover','industry_turnover','cash_equiv_to_interest_debt','cfo','simple_fcf','capex_cash']:
            coverage[key]=dict(status='available',refs=[i+':'+fields.get(key,'metric:'+key) for i in ids],reason='2C企业采用存货周转' if key=='industry_turnover' else '')
            if key=='industry_turnover':coverage[key]['focus']='inventory'
        for k in ['gross_margin','asset_turnover']:
            coverage[k+'_peers']=dict(status='available',refs=[f'P{i}_2025:metric:{k}' for i in range(1,4)],reason='明确虚构同行，完全相同口径')
        report=dict(contract_version=2,workpapers='analysis.json',mode='full',target_ticker='TARGET',target_record_ids=ids,
            company='虚构公司',ticker='TARGET',period='2021–2025',as_of='2026-10-01',basis='模拟数据，禁止用于投资',
            main_report_coverage=coverage,roe_assessment=dict(workpaper='assessment.json',quality=fact('模拟质量解释'),stability_comment=fact('模拟稳定性解释')),
            summary=dict(conclusions=[fact('模拟结论') for _ in range(3)],questions=['模拟问题1','模拟问题2','模拟问题3'],anomaly_note='模拟数据不判断风险',
                indicators=[dict(label='模拟扣非ROE',ref='TARGET_2025:metric:roe_adjusted_parent',scale=100,unit='%',change='不变',explanation='模拟')]),
            sections=[dict(id=i,title=i,conclusions=[fact('模拟结论')],charts=[copy.deepcopy(chart)],status='正常',status_reason='模拟') for i in SECTION_IDS],
            questions=['模拟问题1','模拟问题2','模拟问题3'],appendix_tables=[])
        html=Renderer(report,path).render()
        assert '50/100' in html and '扣非ROE综合评估' in html
        badreport=copy.deepcopy(report);del badreport['main_report_coverage']['sales_cash_ratio']
        try:Renderer(badreport,path).render()
        except ValueError:pass
        else:raise AssertionError('Missing mandatory coverage accepted')
        badreport=copy.deepcopy(report);badreport['main_report_coverage']['gross_margin_peers']['refs']=coverage['gross_margin_peers']['refs'][:2]
        try:Renderer(badreport,path).render()
        except ValueError:pass
        else:raise AssertionError('Only two peers accepted as complete')
        # Strict v3 requires complete data display and each section's own financial evidence.
        strict=copy.deepcopy(report);strict.update(contract_version=3,business_model='b2c')
        extra={'roe_parent':'metric:roe_parent','dupont_adjusted':'metric:dupont_adjusted_parent','net_profit':'raw:net_profit','parent_profit':'raw:parent_profit','adjusted_parent_profit':'raw:adjusted_parent_profit','cash_equiv_close':'raw:cash_equiv_close','interest_debt_close':'raw:interest_debt_close'}
        for key,suffix in extra.items():strict['main_report_coverage'][key]=dict(status='available',refs=[i+':'+suffix for i in ids],reason='模拟口径')
        strict['main_report_coverage']['dupont_drivers']=dict(status='available',refs=[i+':metric:'+key for i in ids for key in ['adjusted_parent_margin','asset_turnover','parent_equity_multiplier']],reason='模拟三因子')
        section_metrics={'roe':'roe_adjusted','revenue':'revenue','gross_margin':'gross_margin','profit':'net_margin','turnover':'asset_turnover','leverage':'cash_equiv_to_interest_debt','cash_flow':'cfo'}
        for section in strict['sections']:
            if section['id'] not in section_metrics:continue
            key=section_metrics[section['id']];c=section['charts'][0]
            c['series']=[dict(name=key,refs=strict['main_report_coverage'][key]['refs'],scale=100 if key in ['roe_adjusted','gross_margin','net_margin'] else 1)]
            c['unit']='%' if key in ['roe_adjusted','gross_margin','net_margin'] else ('百万元' if key in ['revenue','cfo'] else '次/倍')
            if section['id'] in ['gross_margin','turnover']:
                peerkey=('gross_margin' if section['id']=='gross_margin' else 'asset_turnover')+'_peers'
                pc=copy.deepcopy(chart);pc.update(type='bar',labels=['2025'])
                pc['unit']='%' if section['id']=='gross_margin' else '次'
                pc['series']=[dict(name='模拟同行'+str(j),refs=[ref],scale=100 if section['id']=='gross_margin' else 1) for j,ref in enumerate(strict['main_report_coverage'][peerkey]['refs'])]
                section['charts'].append(pc)
        strict_html=Renderer(strict,path).render()
        assert '主报告核心历史数据' in strict_html and '普通归母ROE' in strict_html
        (path/'report.json').write_text(json.dumps(strict))
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('validate_main_report.py')),str(path/'report.json')],capture_output=True,text=True,check=True)
        assert json.loads(result.stdout)['validation']=='PASS'
        def rejects(candidate):
            try:Renderer(candidate,path).validate_main_contract()
            except ValueError:return
            raise AssertionError('Invalid main report coverage accepted')
        candidate=copy.deepcopy(strict);candidate['sections'][1]['charts']=[chart]
        rejects(candidate)
        for key in ['revenue','cfo','simple_fcf','gross_margin']:
            candidate=copy.deepcopy(strict);candidate['main_report_coverage'][key]=dict(status='not_applicable',refs=[],reason='演示')
            rejects(candidate)
        candidate=copy.deepcopy(strict);candidate['main_report_coverage']['sales_cash_ratio']=dict(status='unavailable',refs=[],reason='演示')
        rejects(candidate)
        candidate=copy.deepcopy(strict);candidate['main_report_coverage']['industry_turnover']['focus']='receivables'
        rejects(candidate)
        candidate=copy.deepcopy(strict);candidate['main_report_coverage']['industry_turnover']['focus']='both'
        rejects(candidate)
        candidate=copy.deepcopy(strict);candidate['main_report_coverage']['revenue']['refs'].append(candidate['main_report_coverage']['revenue']['refs'][0])
        rejects(candidate)
        for key in ['revenue','roe_parent','dupont_drivers','sales_cash_ratio']:
            candidate=copy.deepcopy(strict);candidate['main_report_coverage'][key].update(status='partial',refs=candidate['main_report_coverage'][key]['refs'][:1],reason='模拟缺口')
            rejects(candidate)
        candidate=copy.deepcopy(strict);candidate['main_report_coverage']['gross_margin_peers'].update(status='unavailable',refs=[],reason='模拟缺口')
        rejects(candidate)
        candidate=copy.deepcopy(strict)
        excluded=candidate['main_report_coverage']['gross_margin_peers']['refs'].pop()
        candidate['main_report_coverage']['gross_margin_peers'].update(status='partial',reason='模拟不同业务口径',excluded_refs={excluded:'模拟业务口径不一致，非真实判断'})
        assert '同行不可比数据排除记录' in Renderer(candidate,path).render()
        stale=copy.deepcopy(wp)
        next(n for n in stale['metrics'] if n['id']=='TARGET_2025:metric:gross_margin')['value']=.99
        (path/'analysis.json').write_text(json.dumps(stale))
        rejects(strict)
        (path/'analysis.json').write_text(json.dumps(wp))
        # A seven-year report retains its full history; final assessment uses the last five.
        long_wp=analyze(dataset(range(2021,2028)))
        long_score=assess(long_wp,'TARGET',['P1','P2','P3'],years=list(range(2023,2028)))
        long_report=copy.deepcopy(strict);long_ids=[f'TARGET_{y}' for y in range(2021,2028)]
        long_report['target_record_ids']=long_ids
        for item in long_report['main_report_coverage'].values():
            if not item['refs'] or not item['refs'][0].startswith('TARGET_'):continue
            suffixes=list(dict.fromkeys(ref.split(':',1)[1] for ref in item['refs']))
            item['refs']=[rid+':'+suffix for rid in long_ids for suffix in suffixes]
        for section in long_report['sections']:
            for c in section['charts']:
                for series in c['series']:
                    if series['refs'][0].startswith('TARGET_'):
                        suffix=series['refs'][0].split(':',1)[1]
                        series['refs']=[rid+':'+suffix for rid in long_ids]
                        c['labels']=list(range(2021,2028))
        (path/'analysis.json').write_text(json.dumps(long_wp));(path/'assessment.json').write_text(json.dumps(long_score))
        Renderer(long_report,path).validate_main_contract()
        assert long_score['stability']['years']==5
        (path/'analysis.json').write_text(json.dumps(wp));(path/'assessment.json').write_text(json.dumps(score))
        altered=copy.deepcopy(score);altered['score']=99;(path/'assessment.json').write_text(json.dumps(altered))
        try:Renderer(report,path).render()
        except ValueError:pass
        else:raise AssertionError('Tampered score accepted')
    print('PASS: verified adjusted ROE/DuPont, revenue cash ratio, profit cash content, adjusted share, strict cash coverage, losses/zero/missing inputs, fixed-peer score/ties/policy, report coverage and score reconciliation')

if __name__=='__main__':run()
