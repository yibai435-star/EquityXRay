---
name: model-update
description: 依据最新季报、年报或指引更新已有上市公司预测模型/财务工作簿，追踪实际和假设改动并校验公式。用于“更新XX最新财务模型”“根据Q3更新模型”。只点评季度用earnings-analysis；从零建立DCF用dcf-valuation。
---

# 财务模型更新

## 任务与输入
先解析financial-statement-analysis核心及共享约定：插件布局读取插件根shared/，个人Skill布局从可用目录按frontmatter名称找到核心并读取其shared/data-conventions/conventions.md及shared/report-conventions/conventions.md（可用核心scripts/resolve_module.py）。不要猜物理安装目录。核心缺失时明确缺少共享依赖，仍完成可独立核实的工作；不得声称完成整套插件流程。
本阶段提供独立任务入口与研究流程骨架；详细步骤见[工作流](references/workflow.md)。按任务获取公司、期间/基准日与已有资料，已提供信息不重复询问。

## 执行
按核心shared/module-invocation.md区分独立任务与主报告内部支持；支持调用只回传请求证据并嵌回原章节，独立调用保留本模块完整交付。
定位已有模型与版本→检查结构和公式→获取新披露→映射实际数据→区分事实替换和假设修改→重算与对账→生成修订记录并交付更新文件。
先完成可独立进行的研究；关键数据缺失明确具体影响，不能编造数字、预测或已经执行的动作。

## 输出
更新后的原格式模型、逐项变更记录与校验结果；所有文件保存按通用文件约定。没有原模型时先准备数据和映射需求，再索取文件，不声称模型已更新。
组合任务沿核心路由契约交接来源、期间、口径、假设、校验及未决问题。
