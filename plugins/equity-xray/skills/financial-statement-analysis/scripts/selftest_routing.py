#!/usr/bin/env python3
import json
from route_request import route_request

CASES=[
 ('分析XX财报以及比较XX和YY经营模式',[('financial-statement-analysis','full'),('comps-analysis','operating')]),
 ('先分析XX财报，再给XX做DCF',[('financial-statement-analysis','full'),('dcf-valuation','dcf')]),
 ('帮我分析XX财报，同时做XX的DCF估值',[('financial-statement-analysis','full'),('dcf-valuation','dcf')]),
 ('分析XX过去5年财报，并单独做最新季度业绩点评',[('financial-statement-analysis','full'),('earnings-analysis','earnings')]),
 ('分析XX财报并补充最新季度业绩',[('financial-statement-analysis','full')]),
 ('分析XX最新季度财报',[('earnings-analysis','earnings')]),
 ('帮我做XX财务体检',[('financial-statement-analysis','full')]),
 ('分析XX财报并做DCF',[('financial-statement-analysis','full'),('dcf-valuation','dcf')]),
 ('分析XX财报，同时更新XX模型',[('financial-statement-analysis','full'),('model-update','update')]),
 ('给XX做DCF并更新XX模型',[('dcf-valuation','dcf'),('model-update','update')]),
 ('分析财报，再比较同行',[('financial-statement-analysis','full'),('comps-analysis','operating')]),
 ('做XX财务分析报告，不做DCF',[('financial-statement-analysis','full')]),
 ('做XX财务分析报告但不要做DCF',[('financial-statement-analysis','full')]),
 ('分析XX过去5年财报并补充最新季度业绩',[('financial-statement-analysis','full')]),
 ('只做同行估值，不要财报分析',[('comps-analysis','valuation')]),

 ('做XX财务分析报告，毛利率和资产周转率要同行比较',[('financial-statement-analysis','full')]),
 ('做XX财务分析报告并补充最新季度业绩',[('financial-statement-analysis','full')]),
 ('分析XX公司过去5年财报',[('financial-statement-analysis','full')]),
 ('深挖XX公司存货问题',[('financial-statement-analysis','deep')]),
 ('XX公司最新季度业绩怎么样',[('earnings-analysis','earnings')]),
 ('XX和YY谁的经营模式差异更大',[('comps-analysis','operating')]),
 ('给XX做DCF',[('dcf-valuation','dcf')]),
 ('更新XX最新财务模型',[('model-update','update')]),
 ('分析财报，然后做DCF',[('financial-statement-analysis','full'),('dcf-valuation','dcf')]),
 ('根据最新Q3更新汇顶科技模型',[('model-update','update')]),
 ('对比XX与YY的估值倍数',[('comps-analysis','valuation')]),
 ('分析XX过去5年财报，不要做DCF',[('financial-statement-analysis','full')]),
 ('快速分析XX',[('financial-statement-analysis','quick')])]

def main():
    results=[]
    for request,expected in CASES:
        actual=route_request(request)
        assert actual['status']=='matched',(request,actual)
        assert [(x['skill'],x['mode']) for x in actual['workflow']]==expected,(request,actual)
        results.append({'request':request,**actual,'test':'PASS'})
    supported=route_request('做XX财务分析报告，毛利率和资产周转率要同行比较，并补充最新季度业绩')
    assert {x['skill'] for x in supported['support']}=={'comps-analysis','earnings-analysis'}
    assert all(x['delivery']=='embedded_in_main_report' for x in supported['support'])
    assert route_request('今天天气怎么样')['status']=='needs_semantic_routing'
    print(json.dumps({'cases':results,'unknown_fallback':'PASS'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
