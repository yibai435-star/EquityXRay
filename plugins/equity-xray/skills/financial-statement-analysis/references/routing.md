# 路由与组合任务

模块名/状态唯一清单位于shared/routing.json；语义路由须理解请求目的、否定和已有上下文，不机械套关键词。scripts/route_request.py仅验证常见表达的有限回归集，unknown不得冒充已成功路由。

|任务意图|入口与模式|
|---|---|
|过去数年财报、财务质量、三表；深挖存货/ROE等|financial-statement-analysis full/quick/deep|
|最新或指定季度发布解读|earnings-analysis|
|两家公司经营模式、竞争或横向财务比较|comps-analysis operating|
|同行估值/倍数比较|comps-analysis valuation|
|DCF/公司现金流估值|dcf-valuation|
|更新已有模型，即使提到Q3|model-update|

用户明确组合顺序则保留顺序，例如“分析财报，然后做DCF”先financial-statement-analysis再dcf-valuation；没有强制重跑已完成步骤。模型更新里的季度数据属于输入，不自动附加完整earnings报告。单指标深挖不重跑七步；对比不机械跑七步。

## 交接
读取共享数据约定的handoff字段。上游交已核实数据、图表/底稿路径、数据版本、检查、事实、解释和未决问题；下游先验证期间/口径/重大FAIL再继续。分析发现不能直接成为DCF假设。不同模块共享引用，不复制维护指标定义。

## 定位和扩展
个人Skill目录按SKILL.md frontmatter的name解析；插件布局按skills/<name>解析。resolve_module.py可列出已具备模块和shared路径。新增模块先定义独立意图、输入输出、状态和交接，再更新routing.json及最小回归集；不修改财务计算器。
