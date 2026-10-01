#!/usr/bin/env python3
"""Validate financial-report coverage without generating a document or drawing charts."""
import argparse
import json
from pathlib import Path
from render_report import Renderer


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');a=p.parse_args()
    path=Path(a.input).resolve();report=json.loads(path.read_text(encoding='utf-8'))
    if report.get('mode') not in ['full','quick']:
        raise ValueError('This gate applies to main full/quick reports, not independent deep/compare workflows')
    if report.get('contract_version',3)<3:
        raise ValueError('New deliveries require contract_version=3; legacy contracts are for reproduction only')
    renderer=Renderer(report,path.parent);renderer.validate_main_contract()
    print(json.dumps({'validation':'PASS','contract_version':3,'target':report['target_ticker'],
        'coverage':{k:v['status'] for k,v in report['main_report_coverage'].items()},
        'assessment':renderer.assessment['component_status'],
        'scope':'Coverage, fiscal windows, metric evidence, chart references and score reconciliation; business causality and visual quality still need review'},ensure_ascii=False))

if __name__=='__main__':main()
