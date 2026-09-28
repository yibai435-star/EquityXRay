---
name: financial-statement-analysis
description: 分析上市公司过去3–5年或更长周期的财务表现、三张表与财务质量，递归深挖ROE、毛利率、存货和现金流异常，映射到经营战略。用于“分析XX公司2021–2025”“做财务分析”“过去几年发生了什么”“快速分析”“深挖某指标”。原名analyze-listed-company-financials。最新季度点评、同行比较、DCF和模型更新分别交由专项Skill。
---

# 上市公司财报分析

## 1. Skill Purpose
分析增长、盈利、周转、杠杆、现金流质量与财务异常，最终解释业务和战略问题。保留既有方法，不做基础会计教学、单纯摘数、DCF、单季度点评或单纯同行估值。

## 2. Trigger与任务路由
接受完整分析、快速分析、单指标深挖；先核实公司主体和已披露期间，默认最近3–5个完整财年，必要时延长。
最新季度点评→`earnings-analysis`；经营模式/同行估值比较→`comps-analysis`；公司估值→`dcf-valuation`；更新已有预测模型→`model-update`。
组合任务按[路由及交接契约](references/routing.md)依次执行，复用底稿；“更新Q3模型”优先模型更新。深挖仅展开目标指标；快速版保留5–8张关键图。

## 3. Core Workflow
**ROE/杜邦→收入增长→毛利率→费用与净利润→资产周转→财务杠杆→现金流与利润质量→异常扫描→财务到业务/战略解释。**
先按[数据约定](../../shared/data-conventions/conventions.md)取数和溯源，核对[会计调整](references/accounting-adjustments.md)与[跨表验证](references/cross-statement-validation.md)，再解释变化。
按问题读取[指标树](references/metric-tree.md)、[异常识别](references/anomaly-detection.md)、[同行选择](references/peer-comparison.md)、[图表选择](references/chart-guide.md)、[业务解释](references/business-interpretation.md)。特殊行业另读[行业适配](references/sector-adaptations.md)。
确定性计算复用`scripts/calculate_financial_ratios.py`、`scripts/dupont_analysis.py`；接口见[计算契约](references/io-contract.md)。绘图、表格、文件渲染优先调用[通用能力](references/runtime-integration.md)。

## 4. 核心分析哲学
**先总后分、异常优先、图表驱动、跨表验证。** 正常指标简要解释后通过；异常进入递归，禁止平均分配篇幅。
整体指标→找异常→拆一级驱动→找主要贡献→拆二级指标→跨三表验证→查询业务证据→形成经营解释。
直到主要变化获得解释、继续拆解不改变判断或数据不足时停止，记录残差、替代解释和待验证证据。事实与推断分开，异常不等于造假。

## 5. Output Contract
完整报告顺序：Executive Summary；ROE与杜邦；收入；毛利率；费用与净利润；资产周转；杠杆；现金流；异常扫描；财务→业务解释；待验证问题；数据附录。
每个核心步骤原则上有图，图下有发现、解读、是否继续拆解；缺数据说明原因。正常项短写，异常项重点展开，最终按[报告模板](references/report-template.md)及[质量门](references/quality-gates.md)交付。
默认自包含HTML＋可复核Excel/CSV＋结构化JSON；用[共享报告约定](../../shared/report-conventions/conventions.md)保存和交付。仅用户明确要求时制作8–12页汇报PPT；本次格式指示优先。
