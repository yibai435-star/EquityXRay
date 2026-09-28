#!/usr/bin/env python3
import json
from route_request import route_request

CASES=[
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
    assert route_request('今天天气怎么样')['status']=='needs_semantic_routing'
    print(json.dumps({'cases':results,'unknown_fallback':'PASS'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
