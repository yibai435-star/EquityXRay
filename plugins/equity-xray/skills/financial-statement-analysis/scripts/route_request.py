#!/usr/bin/env python3
"""Bounded routing regression aid; natural-language semantic routing stays with the agent."""
import argparse
import json
import re
from pathlib import Path
from resolve_module import resolve_modules


def route_request(request):
    shared=Path(resolve_modules()['shared'])
    spec=json.loads((shared/'routing.json').read_text(encoding='utf-8'))
    # Remove explicit negative clauses in the supported expression set.
    clauses=re.split(r'[，,。；;]|但是|但',request)
    active=[c for c in clauses if not re.match(spec['negative_clause_pattern'],c)]
    steps=re.split(spec['sequence_pattern'], '，'.join(active))
    result=[]; support=[]
    for step in steps:
        chosen=None
        rules = spec['regression_rules']
        if (re.search(spec['main_report_pattern'], step) or re.search(spec['main_report_with_support_pattern'], step, re.I)) and not re.search(r'(更新|修订|修改).*模型', step):
            rules = sorted(rules, key=lambda r: r['skill'] != 'financial-statement-analysis')
        for rule in rules:
            if re.search(rule['pattern'],step,re.I):
                mode=rule['mode']
                for override in rule.get('mode_overrides',[]):
                    if re.search(override['pattern'],step,re.I):mode=override['mode'];break
                chosen={'skill':rule['skill'],'mode':mode};break
        if chosen and (not result or result[-1]!=chosen):
            result.append(chosen)
            if chosen['skill']=='financial-statement-analysis' and chosen['mode']!='deep':
                for rule in spec['embedded_support']:
                    if re.search(rule['pattern'],step,re.I):
                        support.append({'step':len(result)-1, **{k:v for k,v in rule.items() if k!='pattern'},'delivery':'embedded_in_main_report'})
        elif step.strip() and not chosen:
            return {'status':'needs_semantic_routing','workflow':result,'support':support,'unresolved':step,'note':'Do not infer completeness from this bounded parser.'}
    return {'status':'matched' if result else 'needs_semantic_routing','workflow':result,'support':support}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('request');a=p.parse_args()
    print(json.dumps(route_request(a.request),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
