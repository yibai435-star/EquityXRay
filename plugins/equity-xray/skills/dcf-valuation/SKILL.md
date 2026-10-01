---
name: dcf-valuation
description: 对上市公司构建DCF或贴现现金流估值，检验经营假设、WACC、终值与敏感性。用于“给XX做DCF”“做公司估值”。单纯同行倍数用comps-analysis，更新现有工作簿用model-update。
---

# DCF估值

## 任务与输入
先解析financial-statement-analysis核心及共享约定：插件布局读取插件根shared/，个人Skill布局从可用目录按frontmatter名称找到核心并读取其shared/data-conventions/conventions.md及shared/report-conventions/conventions.md（可用核心scripts/resolve_module.py）。不要猜物理安装目录。核心缺失时明确缺少共享依赖，仍完成可独立核实的工作；不得声称完成整套插件流程。
本阶段提供独立任务入口与研究流程骨架；详细步骤见[工作流](references/workflow.md)。按任务获取公司、期间/基准日与已有资料，已提供信息不重复询问。

## 执行
按核心shared/module-invocation.md区分独立任务与主报告内部支持；支持调用只回传请求证据并嵌回原章节，独立调用保留本模块完整交付。
界定估值对象和基准日→验证历史底稿→建立业务预测及情景→预测自由现金流→确定匹配的折现率→计算终值及估值桥接→敏感性和模型校验。
先完成可独立进行的研究；关键数据缺失明确具体影响，不能编造数字、预测或已经执行的动作。

## 输出
估值研究HTML、保留可计算公式的模型和假设/来源底稿。此入口是流程骨架；调用通用表格能力构建模型，不冒称附带完整估值引擎。
组合任务沿核心路由契约交接来源、期间、口径、假设、校验及未决问题。
