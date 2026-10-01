# EquityXRay

> **See beyond the numbers.**  
> **降低研究门槛，不降低研究标准。**

An open-source equity research workflow plugin for ChatGPT Work, ChatGPT Desktop, and Codex. Start with a chart-led financial report to understand a listed company, then use specialist workflows when a question needs deeper research.

EquityXRay帮助非专业人士根据公开财报初步了解一家上市公司。首要交付是近3–5年的带图财务分析报告：看增长有没有收到现金、产品赚不赚钱、资产是否有效使用、利润是否转成现金，以及股东回报来自哪里。需要深入研究时，再调用季度点评、同行比较、DCF或模型更新；主报告也可以按需要调用专项工作流并复用底稿。

## 核心方法

财报分析遵循：先总后分、异常优先、图表驱动、跨表验证。

正常指标快速通过；重要异常在主报告识别主要驱动并跨三张表验证，完整递归深挖作为按需任务。财务变化最终回到产品、市场、竞争、运营和战略解释。

## 主报告必查（v0.2.0）

| 步骤 | 核心指标与比较 |
| --- | --- |
| 股东回报 | 扣非ROE与普通ROE分列、扣非杜邦；近3–5年，默认5年 |
| 收入增长 | 收入、YoY/CAGR、销售实际收现/营业收入 |
| 产品盈利 | 毛利率历史＋3–5家可比同行 |
| 净利润质量 | 销售净利率、CFO/合并净利润、扣非归母/归母净利润 |
| 资产效率 | 总资产周转率历史＋3–5家同行；2C优先存货、2B优先应收周转 |
| 债务覆盖 | 现金及现金等价物/有息债务；经营负债与融资负债区分 |
| 综合评估 | 扣非ROE分数、质量（赚钱机制）、稳定性（近五年变化） |

分数是透明的固定同行相对位置分，不能替代绝对盈利、质量或稳定性判断。数据不足暂不评分。Non-GAAP不自动等于扣非利润；广义cash position不自动等于现金及等价物；亏损/零利润不能机械解释现金含量。所有重要数据与缺口均可追溯。

## 包含的 Skills

| Skill | 用途 |
| --- | --- |
| `financial-statement-analysis` | 首要入口：带图财务体检与扣非ROE评估；明确请求时支持独立指标深挖 |
| `earnings-analysis` | 最新或指定季度业绩、预期和指引差异 |
| `comps-analysis` | 经营模式、竞争定位或同行估值比较 |
| `dcf-valuation` | DCF预测、WACC、终值、桥接和敏感性 |
| `model-update` | 根据最新披露更新已有财务模型 |

## 在 ChatGPT Desktop / Codex 中安装

本仓库提供 repo marketplace。添加Marketplace：

```bash
codex plugin marketplace add yibai435-star/EquityXRay --ref main
```

随后重启 ChatGPT Desktop，打开 **Plugins Directory**，选择 **EquityXRay Plugins** 来源并安装 **EquityXRay**。

也可以克隆仓库后添加本地目录：

```bash
git clone https://github.com/yibai435-star/EquityXRay.git
codex plugin marketplace add ./EquityXRay
```

## 典型请求

- `分析汇顶科技2019–2025`
- `深挖汇顶科技的存货问题`
- `汇顶科技Q3刚发布，分析一下`
- `汇顶科技和兆易创新的经营模式有什么差异`
- `给汇顶科技做DCF`
- `根据最新Q3更新汇顶科技模型`

## 输出与边界

- 完整财务分析默认生成带图的HTML研究报告和可复核Excel/CSV、JSON底稿。
- DCF与模型更新工作流优先调用通用表格能力，保留公式、来源、假设和校验轨迹。
- 数据不足时明确缺口，不虚构数据、预期、目标价或已经执行的动作。
- 异常信号不直接等同于财务造假。
- 本项目是研究工作流和计算工具，不构成投资建议。

## 项目结构

```text
.agents/plugins/marketplace.json
plugins/equity-xray/
├── plugin.json
├── skills/
│   ├── financial-statement-analysis/
│   ├── earnings-analysis/
│   ├── comps-analysis/
│   ├── dcf-valuation/
│   └── model-update/
└── shared/
```

## 可复核计算

核心Skill的`scripts/`包含财务比率、普通/扣非杜邦、扣非ROE同行位置及稳定性统计。分析决策由Skill负责，计算由脚本复算，取数、绘图和文件生成复用环境通用能力。

```bash
python plugins/equity-xray/skills/financial-statement-analysis/scripts/selftest.py
python plugins/equity-xray/skills/financial-statement-analysis/scripts/selftest_main_report.py
python plugins/equity-xray/skills/financial-statement-analysis/scripts/selftest_routing.py
```

四个专项Skill提供独立工作流，依赖通用研究与表格能力；项目不宣称连接付费数据库或自带完整实时估值引擎。

## License

MIT License。可使用、修改、再分发和商业使用，但须保留版权声明与许可证文本。

## Disclaimer

This project is provided for research and educational purposes only. It does not constitute investment advice. Financial data and analytical conclusions should be independently verified before use.

本项目仅用于研究与教育，不构成投资建议。使用财务数据及分析结论前应进行独立复核。
