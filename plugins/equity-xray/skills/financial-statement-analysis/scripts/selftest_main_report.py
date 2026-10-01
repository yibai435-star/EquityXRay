#!/usr/bin/env python3
"""Synthetic integration checks for the initial-report contract; no real-company evidence."""
import copy
import json
import math
import tempfile
from pathlib import Path
from selftest import fixture
from calculate_financial_ratios import analyze
from assess_adjusted_roe import assess
from render_report import Renderer, SECTION_IDS


def dataset():
    d=fixture(); base=d['records'][0]; d['records']=[]
    for ticker, adj in [('TARGET',7),('P1',4),('P2',7),('P3',10)]:
        for year in range(2021,2026):
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
            if year>2021:r['prior_record_id']=f'{ticker}_{year-1}'
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
        for k in ['gross_margin','asset_turnover']:
            coverage[k+'_peers']=dict(status='available',refs=[f'P{i}_2025:metric:{k}' for i in range(1,4)],reason='明确虚构同行，完全相同口径')
        report=dict(contract_version=2,workpapers='analysis.json',mode='full',target_ticker='TARGET',target_record_ids=ids,
            company='虚构公司',ticker='TARGET',period='2021–2025',as_of='2026-10-01',basis='模拟数据，禁止用于投资',
            main_report_coverage=coverage,roe_assessment=dict(workpaper='assessment.json',quality=fact('模拟质量解释'),stability_comment=fact('模拟稳定性解释')),
            summary=dict(conclusions=[fact('模拟结论') for _ in range(3)],questions=['模拟问题1','模拟问题2','模拟问题3'],anomaly_note='模拟数据不判断风险',
                indicators=[dict(label='模拟扣非ROE',ref='TARGET_2025:metric:roe_adjusted_parent',scale=100,unit='%',change='不变',explanation='模拟')]),
            sections=[dict(id=i,title=i,conclusions=[fact('模拟结论')],charts=[chart],status='正常',status_reason='模拟') for i in SECTION_IDS],
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
        altered=copy.deepcopy(score);altered['score']=99;(path/'assessment.json').write_text(json.dumps(altered))
        try:Renderer(report,path).render()
        except ValueError:pass
        else:raise AssertionError('Tampered score accepted')
    print('PASS: verified adjusted ROE/DuPont, revenue cash ratio, profit cash content, adjusted share, strict cash coverage, losses/zero/missing inputs, fixed-peer score/ties/policy, report coverage and score reconciliation')

if __name__=='__main__':run()
