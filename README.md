# EquityXRay

> **See beyond the numbers.**  
> **降低研究门槛，不降低研究标准。**

An open-source equity research plugin for ChatGPT Work, ChatGPT Desktop, and Codex. Turn public filings into evidence-backed financial diagnostics, business insights, peer comparisons, DCF valuations, and model updates.

EquityXRay把长期财务体检与季度点评、同行比较、DCF、模型更新拆成五个可独立触发、又能共享底稿的工作流。它不会机械复述财报，而是把公开披露转化为可验证、可追溯、可继续深挖的上市公司研究结论。

## 核心方法

财报分析遵循：先总后分、异常优先、图表驱动、跨表验证。

正常指标快速通过；异常指标沿指标树递归拆解，并用资产负债表、利润表、现金流量表及业务证据交叉验证。财务变化最终回到产品、市场、竞争、运营和战略解释。

## 包含的 Skills

| Skill | 用途 |
| --- | --- |
| `financial-statement-analysis` | 3–5年或更长周期的财务表现、异常和业务解释 |
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

## License

MIT License。可使用、修改、再分发和商业使用，但须保留版权声明与许可证文本。

## Disclaimer

This project is provided for research and educational purposes only. It does not constitute investment advice. Financial data and analytical conclusions should be independently verified before use.

本项目仅用于研究与教育，不构成投资建议。使用财务数据及分析结论前应进行独立复核。
