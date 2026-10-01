---
name: financial-statement-analysis
description: 生成上市公司近3–5年财务初步诊断报告，以扣非ROE为主线，覆盖收入收现、同行毛利与周转、利润现金含量、债务现金覆盖及回报质量和稳定性。用于“分析XX财报”“做财务分析”“财务质量”“快速分析”；兼容显式“深挖某指标”的独立研究模式。季度点评、独立同行比较、DCF和模型更新分别衔接专项Skill。
---

# 上市公司财报分析

## 1. Skill Purpose
首要交付为帮助非专业人士初步了解公司的财务分析报告：判断增长、盈利、周转、杠杆和现金质量，最终综合评估扣非ROE的分数、赚钱机制与稳定性。深入研究按需衔接专项工作流，不让主报告膨胀为无边界的战略研究。

## 2. Trigger与任务路由
接受完整分析、快速分析、单指标深挖；先核实公司主体和已披露期间，默认最近3–5个完整财年，必要时延长。
最新季度点评→`earnings-analysis`；经营模式/同行估值比较→`comps-analysis`；公司估值→`dcf-valuation`；更新已有预测模型→`model-update`。
组合任务按[路由及交接契约](references/routing.md)依次执行，复用底稿；“更新Q3模型”优先模型更新。深挖仅展开目标指标；快速版保留5–8张关键图。

## 3. Core Workflow
**扣非ROE/杜邦→收入及收现→毛利率及同行→净利润及现金质量→资产周转及同行/行业分支→财务杠杆→现金流验证→异常简扫→业务解释→扣非ROE综合评估。**
完整与快速报告必须先读取[主报告必选指标](references/main-report-contract.md)；确定性公式只维护于[指标定义](references/metric-definitions.md)。默认每个核心指标展示近3–5年，毛利率和总资产周转率均比较3–5家同行；具体缺口如实标记。
先按[数据约定](../../shared/data-conventions/conventions.md)取数和溯源，核对[会计调整](references/accounting-adjustments.md)与[跨表验证](references/cross-statement-validation.md)，再解释变化。
按问题读取[指标树](references/metric-tree.md)、[异常识别](references/anomaly-detection.md)、[同行选择](references/peer-comparison.md)、[图表选择](references/chart-guide.md)、[业务解释](references/business-interpretation.md)。特殊行业另读[行业适配](references/sector-adaptations.md)。
确定性计算复用`scripts/calculate_financial_ratios.py`、`scripts/dupont_analysis.py`；综合评估按[评估规则](references/roe-assessment.md)调用`scripts/assess_adjusted_roe.py`。接口见[计算契约](references/io-contract.md)，执行交给[通用能力](references/runtime-integration.md)。

## 4. 核心分析哲学
**先总后分、异常优先、图表驱动、跨表验证。** 正常指标简要解释后通过；异常进入递归，禁止平均分配篇幅。
主报告：整体指标→异常→一级驱动→至少两表验证→简明经营解释→下一阶段问题。只展开会改变初步判断的主要异常；显式深挖任务才沿指标树递归多层。可调用comps/earnings等取证并将结果嵌回主报告，不自动附送完整专项报告。
区分普通ROE、法定扣非ROE、分析调整ROE及Non-GAAP；缺口不能互相替代。事实与推断分开，异常不等于造假。

## 5. Output Contract
完整报告顺序：Executive Summary；扣非ROE与杜邦；收入及收现；毛利率及同行；净利润质量；周转及同行/行业分支；杠杆；现金流；异常简扫；业务解释；扣非ROE综合评估（分数/质量/稳定性）；待验证问题；数据附录。
每个核心步骤原则上有图，图下有发现、解读、是否继续拆解；缺数据说明原因。正常项短写，异常项重点展开，最终按[报告模板](references/report-template.md)及[质量门](references/quality-gates.md)交付。
默认自包含HTML＋可复核Excel/CSV＋结构化JSON；用[共享报告约定](../../shared/report-conventions/conventions.md)保存和交付。仅用户明确要求时制作8–12页汇报PPT；本次格式指示优先。
