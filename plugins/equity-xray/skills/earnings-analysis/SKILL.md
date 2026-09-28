---
name: earnings-analysis
description: 分析上市公司最新季度或指定季度业绩、财报发布点评、实际与预期/指引差异及业绩电话会。用于“Q3刚发布”“最新季度业绩怎么样”。多年度体检用financial-statement-analysis；修改已有模型用model-update。
---

# 季度业绩分析

## 任务与输入
先解析financial-statement-analysis核心及共享约定：插件布局读取插件根shared/，个人Skill布局从可用目录按frontmatter名称找到核心并读取其shared/data-conventions/conventions.md及shared/report-conventions/conventions.md（可用核心scripts/resolve_module.py）。不要猜物理安装目录。核心缺失时明确缺少共享依赖，仍完成可独立核实的工作；不得声称完成整套插件流程。
本阶段提供独立任务入口与研究流程骨架；详细步骤见[工作流](references/workflow.md)。按任务获取公司、期间/基准日与已有资料，已提供信息不重复询问。

## 执行
核实季度、披露时间和合并范围→整理实际/可比期/发布前预期/公司指引→识别超预期或不及预期的具体项→拆业务驱动→验证现金与一次性项目→提出预测或研究影响。
先完成可独立进行的研究；关键数据缺失明确具体影响，不能编造数字、预测或已经执行的动作。

## 输出
季度研究HTML简报、关键指标比较表与可复核底稿；按重要问题选图。未取得发布前预期时不写“超预期”。不自动修改预测模型。
组合任务沿核心路由契约交接来源、期间、口径、假设、校验及未决问题。
