# 模块调用契约

本文件唯一维护调用关系，数据口径和报告格式仍分别由data-conventions、report-conventions负责。模块清单及回归规则由routing.json维护。

## standalone：独立任务
用户主要请求季度、对比、DCF或模型更新时，直接进入相应模块并交付该模块的完整成果。不强制先跑财报主报告。明确组合任务保留顺序及所有交付，复用已核实数据而不重复研究。

## support：主报告内部协作
主报告仍由financial-statement-analysis负责：需要同行证据时调用comps，需要季度补充时调用earnings；专项结果嵌回相应正文。此调用不自动附带另一份完整专项报告，也不扩大成估值/更新模型任务。

调用请求至少带：
- `role`: standalone或support；`from_module`、`to_module`。
- `company/ticker`、`as_of`、`periods`、币种/单位/范围、`data_version`。
- `question`、`requested_metrics`、`target_sections`、已有证据/底稿。
- `scope`: 需要哪些结果、哪些缺口会影响结论；不能传隐含“把所有方向查到底”。

返回至少带：
- `status`: complete/partial/blocked；所需证据完成情况与具体限制。
- 原始数据/派生指标引用、来源与页码、口径及可比性说明。
- 财务事实、公司解释、外部证据、推断分开；给主要替代解释。
- `target_sections`映射、待验证问题、影响正文判断的缺口。

没有付费库、原模型或一致预期时如实降级，不宣称调用成功即数据齐全。调用状态与经营异常状态分开。下游读到重大相关FAIL时修正或标限制；不能将上游推断直接用作DCF预测假设。

## 研究预算
正常指标快速通过。异常支持任务只解决会改变主报告初步结论的问题；完成一级驱动与跨表验证后，将剩余问题列作后续研究。显式deep任务才继续递归。模块调用不能形成无终点循环；重复调用须说明新证据或未解决问题。
