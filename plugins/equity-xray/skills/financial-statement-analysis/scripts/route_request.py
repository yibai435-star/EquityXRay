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
    clauses=re.split(r'[，,。；;]',request)
    active=[c for c in clauses if not re.match(r'^\s*(不要|不用|不需要|别)',c)]
    steps=re.split(r'然后|再(?=做|分析|更新)|接着', '，'.join(active))
    result=[]
    for step in steps:
        chosen=None
        for rule in spec['regression_rules']:
            if re.search(rule['pattern'],step,re.I):
                mode=rule['mode']
                for override in rule.get('mode_overrides',[]):
                    if re.search(override['pattern'],step,re.I):mode=override['mode'];break
                chosen={'skill':rule['skill'],'mode':mode};break
        if chosen and (not result or result[-1]!=chosen):result.append(chosen)
        elif step.strip() and not chosen:
            return {'status':'needs_semantic_routing','workflow':result,'unresolved':step,'note':'Do not infer completeness from this bounded parser.'}
    return {'status':'matched' if result else 'needs_semantic_routing','workflow':result}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('request');a=p.parse_args()
    print(json.dumps(route_request(a.request),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
