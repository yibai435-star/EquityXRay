# ChatGPT Work适配与兼容

1. 财报主Skill决定看什么/怎么比较/何时拆，不内置外部账户或Claude运行时依赖。
2. 可用Data Analytics、Spreadsheets、Web、文件、Python/Notebook与报告技能各司其职；先加载相关通用技能再用其能力。纯文档型HTML请求不自动变成网站发布任务。
3. `calculate_financial_ratios.py`是现有计算引擎的标准入口；`financials.py`保留兼容导入/旧命令，不复制算法。`dupont_analysis.py`独立提供多期恒等式和贡献分解。公式和输入契约分别见metric-definitions.md、io-contract.md。
4. `render_report.py`与assets原样保留兼容能力，通用报告/图表工具优先；本次仅修正信息标签和待验证问题顺序，不继续开发第二套通用渲染系统。
5. 个人Skill安装模式：按frontmatter名称解析同级技能，财报核心持有唯一shared目录；其余专项Skill读取核心shared。插件包模式：五个技能位于skills/，共享规则位于插件根shared/。
6. `scripts/resolve_module.py`解析两种布局；`scripts/build_plugin.py`由已安装五个技能生成标准equity-research包，构建时重定位共享链接、校验资源。不手工维护分发副本。
7. 核心已可执行；四个专项为独立入口及可执行研究步骤骨架，尚未宣称完成真实公司全链路验收。插件打包成功不等于已注册/安装为目录插件；没有注册工具时明确区分。

## 构建与维护
执行`python3 <core>/scripts/build_plugin.py --out <新目录>/equity-research`生成用户指定架构。生成目录为可重建的交付副本；不要编辑它后回灌规则。唯一源是五个个人Skill、核心shared和assets/plugin.json。新增模块修改注册清单与回归集，构建器自动发现。创建标准plugin.json并不自动授予目录插件注册权限。
