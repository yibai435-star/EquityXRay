#!/usr/bin/env python3
"""Resolve installed personal modules or a portable plugin without installation IDs."""
import argparse
import json
import re
from pathlib import Path


def skill_name(path):
    text=(path/'SKILL.md').read_text(encoding='utf-8')
    match=re.search(r'^name: *([^\n]+)$',text,re.M)
    return match.group(1).strip().strip('"\'') if match else None


def resolve_modules(anchor=None):
    core=Path(anchor or Path(__file__).resolve().parents[1]).resolve()
    if core.parent.name=='skills' and (core.parent.parent/'plugin.json').is_file():
        base=core.parent; shared=base.parent/'shared'
    else:
        base=core.parent; shared=core/'shared'
    modules={}
    for path in sorted(base.iterdir()):
        if not path.is_dir() or not (path/'SKILL.md').is_file():continue
        name=skill_name(path)
        if name in modules:raise ValueError('Duplicate installed module name: '+name)
        if name:modules[name]=str(path)
    return dict(modules=modules,shared=str(shared))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--module');p.add_argument('--anchor');a=p.parse_args()
    result=resolve_modules(a.anchor)
    if a.module:
        if a.module not in result['modules']:raise SystemExit('Module unavailable: '+a.module)
        result={'name':a.module,'path':result['modules'][a.module],'shared':result['shared']}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
