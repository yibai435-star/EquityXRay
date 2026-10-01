#!/usr/bin/env python3
"""Auditable adjusted-ROE peer-position score; qualitative quality stays with research."""
import argparse
import json
import math
import statistics
from datetime import date
from pathlib import Path


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def assess(data, target, peers, basis='average_parent', years=None):
    if years is not None and (len(set(years)) != len(years) or not all(isinstance(y, int) and not isinstance(y, bool) for y in years)):
        raise ValueError('Assessment years must be distinct integers')
    if basis not in ['average_parent', 'reported_weighted']:
        raise ValueError('Use a uniform adjusted-ROE basis')
    if len(set(peers)) != len(peers) or target in peers:
        raise ValueError('Distinct peer tickers must exclude the target')
    nodes = {n['id']: n for group in ['raw', 'metrics'] for n in data[group]}
    records = {}
    for r in data['records']:
        if r['period_type'] != 'FY' or r['ticker'] not in [target, *peers]:
            continue
        key = (r['ticker'], r['period_start'], r['period_end'])
        if key in records:
            raise ValueError('Duplicate company/year: reconcile data versions first')
        records[key] = r
    periods = sorted({(s, e) for t, s, e in records if t == target})
    if years:
        periods = [p for p in periods if int(p[1][:4]) in years]
    else:
        periods = periods[-5:]
    out = dict(schema_version=1, scheme='adjusted_roe_peer_position_v1', target=target,
               peers=peers, basis=basis, score=None, status='unavailable', limitations=[],
               annual=[], stability=None, quality='由研究者结合扣非杜邦、收现和利润现金质量解释，不自动评分')
    requested_years = sorted(years) if years is not None else [int(end[:4]) for start,end in periods]
    missing_years = sorted(set(requested_years)-{int(end[:4]) for start,end in periods})
    out['requested_years'] = requested_years; out['missing_years'] = missing_years
    selected_ids = {r['id'] for (t,start,end),r in records.items() if (start,end) in periods}
    failed_checks = [c for c in data.get('checks', []) if c.get('status') == 'FAIL' and (not c.get('record_id') or c['record_id'] in selected_ids)]
    failed_ids = {c.get('record_id') for c in failed_checks}
    global_failure = any(not c.get('record_id') for c in failed_checks)
    if years is not None and set(years) != {int(end[:4]) for start,end in periods}:
        out['limitations'].append('请求的评估年份存在缺失，不能静默缩短评分窗口')
    if failed_checks:
        out['limitations'].append('底稿存在FAIL，修正勾稽后才能评分')
    if not 3 <= len(peers) <= 5:
        out['limitations'].append('评分要求3–5家固定可比同行')
    if not 3 <= len(periods) <= 5:
        out['limitations'].append('评分要求连续3–5个共同完整财年')
    def observation(r):
        if not r:
            return None, None
        if global_failure or r['id'] in failed_ids:
            return None, None
        suffix = 'metric:roe_adjusted_parent' if basis == 'average_parent' else 'raw:roe_adjusted_reported'
        ref = r['id'] + ':' + suffix
        if r.get('adjusted_profit_basis') not in ['disclosed_nonrecurring', 'analyst_reconciled'] or not r.get('adjustment_policy_id'):
            return None, ref
        # Negative equity cannot produce meaningful return comparisons, including reported ROE.
        equity = [r['values'].get(k, {}).get('value') for k in ['parent_equity_open', 'parent_equity_close']]
        if not all(finite(v) and v > 0 for v in equity):
            return None, ref
        node = nodes.get(ref, {})
        if basis == 'reported_weighted' and node.get('unit') != 'ratio':
            return None, ref
        v = node.get('value')
        return (v if finite(v) else None), ref
    policies, standards, scopes, dependencies = set(), set(), set(), []
    for index, (start, end) in enumerate(periods):
        if index and (int(end[:4]) != int(periods[index-1][1][:4]) + 1 or date.fromisoformat(start).toordinal() != date.fromisoformat(periods[index-1][1]).toordinal() + 1):
            out['limitations'].append('财年不连续；不得挑选有利年份')
        if not 360 <= (date.fromisoformat(end)-date.fromisoformat(start)).days + 1 <= 371:
            out['limitations'].append('期间不是完整财年')
        row = dict(period_start=start, period_end=end, target=None, peers=[], score=None)
        for ticker in [target, *peers]:
            r = records.get((ticker, start, end))
            value, ref = observation(r)
            if r:
                policies.add((r.get('adjusted_profit_basis'), r.get('adjustment_policy_id')))
                standards.add(r.get('accounting_standard')); scopes.add(r.get('scope'))
            if ref:
                dependencies.append(ref)
            if ticker == target:
                row['target'] = dict(value=value, ref=ref, profit_basis=r.get('adjusted_profit_basis') if r else None)
            else:
                row['peers'].append(dict(ticker=ticker, value=value, ref=ref))
        values = [p['value'] for p in row['peers']]
        tv = row['target']['value']
        if tv is not None and len(values) >= 3 and all(v is not None for v in values):
            lower = sum(v < tv and not math.isclose(v, tv, abs_tol=1e-12, rel_tol=0) for v in values)
            tied = sum(math.isclose(v, tv, abs_tol=1e-12, rel_tol=0) for v in values)
            row['score'] = 100 * (lower + .5 * tied) / len(values)
        else:
            out['limitations'].append('缺少同财年、可核实扣非口径或正权益的公司/同行数据：'+end)
        out['annual'].append(row)
    if len(policies) != 1 or len(standards) != 1 or scopes != {'consolidated'}:
        out['limitations'].append('调整政策、准则或报表范围不一致；先完成可比重述')
    target_records = [records.get((target, start, end)) for start, end in periods]
    target_policies = {(r.get('adjusted_profit_basis'), r.get('adjustment_policy_id'), r.get('accounting_standard'), r.get('scope')) for r in target_records if r}
    out['profit_basis'] = next(iter(target_policies))[0] if len(target_policies) == 1 else 'unverified'
    # Stability can use the latest contiguous valid same-policy block; missing earlier years stay explicit.
    block = []
    policy = None
    for row, r in reversed(list(zip(out['annual'], target_records))):
        if not r or row['target']['value'] is None or not 360 <= (date.fromisoformat(row['period_end'])-date.fromisoformat(row['period_start'])).days + 1 <= 371:
            break
        current_policy = (r.get('adjusted_profit_basis'), r.get('adjustment_policy_id'), r.get('accounting_standard'), r.get('scope'))
        if policy is not None and current_policy != policy:
            break
        if block:
            next_row = block[-1]
            if date.fromisoformat(next_row['period_start']).toordinal() != date.fromisoformat(row['period_end']).toordinal() + 1:
                break
        policy = current_policy; block.append(row)
    block.reverse()
    if len(block) >= 3:
        stable_values = [row['target']['value'] for row in block]
        out['stability'] = dict(years=len(stable_values), annual_roe=stable_values,
            period_start=block[0]['period_start'], period_end=block[-1]['period_end'],
            coverage_note=('最新连续同口径有效年段；仅覆盖'+block[0]['period_start']+'至'+block[-1]['period_end']+'；请求缺失年份：'+','.join(map(str,missing_years))) if missing_years else ('最新连续同口径有效年段；其余选择年份不纳入稳定性结论' if len(block) < len(periods) else '完整覆盖所选历史'),
            latest=stable_values[-1], change_pp=(stable_values[-1]-stable_values[0])*100,
            median=statistics.median(stable_values), minimum=min(stable_values), maximum=max(stable_values),
            std_pp=statistics.pstdev(stable_values)*100, positive_years=sum(v>0 for v in stable_values))
    out['stability_limitations'] = (['请求年份未覆盖：'+','.join(map(str,missing_years))] if missing_years else []) if out['stability'] is not None else ['目标公司缺少至少3个截至所选最新财年的连续、完整、同口径且勾稽有效的扣非ROE年份']
    out['component_status'] = {'score':'unavailable', 'stability':('partial' if missing_years or len(block)<len(periods) else 'computed') if out['stability'] is not None else 'unavailable', 'quality':'research_required'}
    if not out['limitations']:
        out['score'] = round(statistics.median(row['score'] for row in out['annual']))
        out['status'] = 'computed'
        out['component_status']['score'] = 'computed'
    if out['status'] != 'computed':
        for row in out['annual']:
            row['score'] = None
    out['limitations'] = sorted(set(out['limitations']))
    out['dependencies'] = dependencies
    out['score_dependencies'] = dependencies
    out['stability_dependencies'] = [row['target']['ref'] for row in block] if out['stability'] is not None else []
    out['source_ids'] = sorted({s for ref in dependencies for s in nodes.get(ref, {}).get('source_ids', [])})
    out['interpretation'] = '0–100为固定同行中的扣非ROE相对位置；不能代替绝对盈利、质量或稳定性判断。亏损公司也可能获得高相对分。'
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input'); p.add_argument('--target', required=True); p.add_argument('--peers', nargs='+', required=True)
    p.add_argument('--basis', choices=['average_parent', 'reported_weighted'], default='average_parent')
    p.add_argument('--years', type=int, nargs='+'); p.add_argument('--out', required=True)
    a=p.parse_args(); result=assess(json.loads(Path(a.input).read_text(encoding='utf-8')),a.target,a.peers,a.basis,a.years)
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'score':result['score'],'limitations':result['limitations']},ensure_ascii=False))

if __name__=='__main__':main()
