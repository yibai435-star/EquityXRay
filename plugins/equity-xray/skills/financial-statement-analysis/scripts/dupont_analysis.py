#!/usr/bin/env python3
"""DuPont identities and exact Shapley changes for validated multi-period data."""
import argparse
import itertools
import json
import math
from pathlib import Path


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def shapley(before, after):
    if len(before) != 3 or len(after) != 3 or not all(number(x) for x in list(before) + list(after)):
        return None
    result = [0.0] * 3
    for order in itertools.permutations(range(3)):
        state = list(before)
        for index in order:
            old = math.prod(state)
            state[index] = after[index]
            result[index] += (math.prod(state) - old) / 6
    return result


def analyze_dupont(data, basis='both'):
    if any(c['status'] == 'FAIL' for c in data.get('checks', [])):
        raise ValueError('Resolve failed workpaper checks before DuPont attribution')
    modes = ['total','parent'] if basis == 'both' else (['total','parent','adjusted_parent'] if basis == 'all' else [basis])
    if not all(b in ['total','parent','adjusted_parent'] for b in modes):
        raise ValueError('basis must be total, parent, adjusted_parent, both or all')
    nodes = {m['id']:m for m in data['metrics']}
    records = {r['id']:r for r in data['records']}
    periods, changes = [], []
    for b in modes:
        keys = ['net_margin' if b=='total' else ('adjusted_parent_margin' if b=='adjusted_parent' else 'parent_margin'), 'asset_turnover',
                'equity_multiplier' if b=='total' else 'parent_equity_multiplier']
        def factors(rid):
            refs = [f'{rid}:metric:{k}' for k in keys]
            values = [nodes.get(ref,{}).get('value') for ref in refs]
            return refs, values
        for r in sorted(records.values(), key=lambda r:(r['ticker'],r['period_end'],r['id'])):
            refs, values = factors(r['id'])
            roe = nodes.get(f'{r["id"]}:metric:roe_{b}',{}).get('value')
            derived = math.prod(values) if all(number(v) for v in values) else None
            if number(derived) and number(roe) and not math.isclose(derived,roe,abs_tol=1e-10,rel_tol=1e-9):
                raise ValueError('DuPont identity mismatch: '+r['id'])
            periods.append(dict(record_id=r['id'],ticker=r['ticker'],period_end=r['period_end'],basis=b,
                                factor_names=keys,factors=values,roe=roe,product=derived,metric_refs=refs,
                                source_ids=sorted({sid for ref in refs for sid in nodes.get(ref,{}).get('source_ids',[])})))
            prior=r.get('prior_record_id')
            if not prior:
                continue
            if prior not in records or any(records[prior][k]!=r[k] for k in ['ticker','period_type','currency','unit','scope','accounting_standard']):
                raise ValueError('Incomparable prior record')
            old_refs, old_values=factors(prior)
            comparable_policy = (b != 'adjusted_parent' or
                                 (r.get('adjustment_policy_id') == records[prior].get('adjustment_policy_id') and
                                  r.get('adjusted_profit_basis') == records[prior].get('adjusted_profit_basis')))
            contribution=shapley(old_values,values) if comparable_policy else None
            total_delta=math.prod(values)-math.prod(old_values) if contribution is not None else None
            if contribution is not None and not math.isclose(sum(contribution),total_delta,abs_tol=1e-10):
                raise ValueError('Contribution sum mismatch')
            changes.append(dict(from_record=prior,to_record=r['id'],basis=b,
                                delta_pp=100*total_delta if total_delta is not None else None,
                                contributions_pp=dict(zip(keys,[v*100 for v in contribution])) if contribution is not None else None,
                                metric_refs=old_refs+refs,note='Mathematical attribution, not causal proof; analytical average-balance ROE'))
    return dict(schema_version=1,periods=periods,changes=changes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis');parser.add_argument('--basis',choices=['total','parent','adjusted_parent','both','all'],default='all');parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=analyze_dupont(json.loads(Path(args.analysis).read_text(encoding='utf-8')),args.basis)
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'periods':len(result['periods']),'changes':len(result['changes']),'out':str(output)},ensure_ascii=False))


if __name__=='__main__':main()
