# 可复核输入输出契约

## 目录
1. 标准输入
2. 字段与计算
3. 报告输入
4. 命令与检查

## 1. 标准输入 input.json
从assets/input.template.json复制到任务工作目录填写。模板中的null是缺失，不是零。不要修改技能里的模板以存储公司资料。

```json
{
  "schema_version": 1,
  "metadata": {"as_of": "2026-09-27", "purpose": "公司财务研究"},
  "sources": [{"id":"S1","title":"公司2025年年度报告","locator":"https://实际官方地址","published_date":"实际披露日","accessed_date":"实际获取日"}],
  "records": [{
    "id":"company_FY2025", "company":"公司全称", "ticker":"代码.交易所",
    "period_start":"2025-01-01", "period_end":"2025-12-31", "period_type":"FY",
    "currency":"CNY", "unit":"百万元", "scope":"consolidated", "accounting_standard":"CAS",
    "values":{"revenue":{"value":null,"source_ids":["S1"],"locator":"PDF第X页，合并利润表","original_label":"营业收入","original_value":null,"original_unit":"元","note":"原始值除以1000000"}}
  }],
  "adjustments":[], "peers":[], "claims":[], "accounting_notes":[], "trend_requests":[]
}
```
示例只有结构，日期、页码、地址、数值必须来自实际资料。每个非空数必须有source_ids、locator和original_label。原始金额/单位保留，value为已统一币种/单位的数据。来源文件可为真实本地路径/Library文件标识；不可捏造URL。

- 一公司一期间一record，同一数据版本；自算使用合并报表。raw记录按字段留来源，派生metrics留formula/dependencies/source_ids，支持全链复算。
- `prior_record_id`显式指定可比上年记录才计算YoY及杜邦贡献；先人工确认合并范围/准则可比。脚本拒绝错币种、错FY/TTM、非相邻财年；52/53周特殊财年另编透明计算，不强套日期。
- 可选`day_basis`统一365或实际天数（默认实际）；`rounding_tolerance`是金额单位内的四舍五入勾稽容差，默认0.01，不是业务异常阈值。不能为消除报错而任意放宽。
- 上年期末与本年期初自动检查衔接；经证实重述可用有来源的`opening_adjustment_科目`表示“本年期初−原上年期末”。无来源不可用调整消除FAIL。
- 期初数据都要显式填写并溯源；不从另一record静默推断。多时点均值、行业扩展、ROIC、量价/分部桥接用额外计算脚本或extra_data记录，遵从公式参考并保留轨迹。

## 2. 字段

| 输入字段 | 含义/约定 |
|---|---|
| revenue, cogs | 收入、营业成本；成本正常为正 |
| net_profit, parent_profit, adjusted_parent_profit, minority_profit | 合并净利、归母、扣非归母、少数股东损益；可正可负 |
| selling_expense, admin_expense, rd_expense, financial_expense | 四项费用；按费用方向，财务费用可为负 |
| profit_before_tax, income_tax, interest_expense | 税前利润、所得税费用、费用化利息；不以财务费用替利息 |
| total_assets_open/close, total_equity_open/close, parent_equity_open/close | 期初末总资产、总权益、归母权益；总权益含少数股东 |
| total_liabilities_close | 总负债 |
| ar_open/close, inventory_open/close | 口径一致的应收/存货净额；纳入票据/合同资产须另标清 |
| trade_payables_open/close, purchases | 贸易应付；可比采购额不可得则DPO用cogs近似并警示 |
| fixed_assets_open/close | 固定资产净额，不静默包括在建工程 |
| interest_debt_close, available_cash_close | 去重后的有息债务、可动用现金；在accounting_notes列构成/排除、含租赁与否 |
| cash_equiv_open/close | 现金流量表现金及等价物，不直接替换货币资金 |
| cfo, cfi, cff, fx_cash_change | 经营/投资/融资现金流和汇率影响，有符号 |
| capex_cash | 购建长期经营资产现金流出，填正；不等于整个投资CF |
| goodwill_close, cip_close | 期末商誉、在建工程，供扩展检查 |
| gross_profit_disclosed | 可选披露毛利，用于核算收入−成本 |
| roe_reported, roe_adjusted_reported | 披露加权/扣非ROE，cell.unit填ratio，值用0.15表示15%；不混自算值 |
| extra_* | 其他原始披露，允许单独unit，供自定义桥接/图表，不自动当货币计算 |

所有默认核心字段金额一致。新增损益科目可自行明确名称/符号，r.bridges支持：
```json
{"name":"归母利润桥接","target":"parent_profit","terms":[{"field":"net_profit","sign":1},{"field":"minority_profit","sign":-1}],"note":"所有项都有原表来源"}
```
terms必须完整、符号±1，target是原始披露字段；未披露项不擅自当0。

多期请求：
```json
{"id":"revenue_cagr_2021_2025","kind":"cagr","record_ids":["Y2021","Y2022","Y2023","Y2024","Y2025"],"field":"revenue"}
```
或`kind:"cumulative_cash_conversion"`同一record_ids；脚本输出summary指标，仍附dependencies。仅FY连续可比序列；跨年中断/合并范围改变先调整，不能硬算。

附属数组全部为对象列表：
- adjustments：id、期间、项目、披露值、税前调整、税效、少数股东、归母影响、调整后值、依据/source_ids。
- peers：公司/代码、核心业务、入选/排除、理由、可比限制、分部归属。
- claims：id、结论、性质、metric_ids/source_ids、替代解释、置信依据、待验证证据。
- accounting_notes：id、主题、口径、数据版本、缺口/限制及来源。

输出包含input.json、analysis.json、raw.csv、metrics.csv、formulas.csv、sources.csv、checks.csv、adjustments.csv、peers.csv、claims.csv、accounting_notes.csv和可选workpapers.xlsx。Excel公式表为可复算表达式和依赖ID，并非自动重算的Excel公式；修改输入后重新运行脚本。若用户需要交互重算，再用Spreadsheets技能构建真实Excel公式。

## 3. report.json
从assets/report.template.json复制。`workpapers`指向analysis.json（相对于report.json目录）。
- 底稿存在FAIL时默认阻止报告生成；只能在确需交付带缺口初稿且明确写`unresolved_check_explanation`时输出，首页展示限制，受影响结论必须降级。
- mode=full/quick/deep/compare；company/ticker/period/as_of/basis填写报告元数据。
- 每个研究陈述对象：`{"text":"结论","kind":"财务事实|公司管理层解释|外部证据|分析推断|研究问题|数据限制","refs":["record:metric:gross_margin"],"source_ids":["S1"]}`。事实、公司管理层解释、外部证据、推断必须有证据，推断引用支撑资料不表示因果已证实。
- summary.conclusions 3–5项、indicators 6–8行（label/ref/scale/unit/change/explanation）、anomalies有证据时2–4项，缺异常用anomaly_note，questions 3–5条。deep/compare可按问题适配长度。
- full九节id按模板不改顺序；每节conclusions/charts/status/status_reason，异常才drilldown。确实缺数据可用data_gap代替图；不可用其跳过有数据步骤。
- chart共同字段title/conclusion/how_to_read/findings/interpretation/drilldown，其中drilldown={needed:true或false,next:下一层或停止理由}。
- line/bar/stacked：unit、labels、series=[{name,refs:[数据ID...],scale:1}]。小数率转%时scale=100；不允许独立手填绘图值，渲染从底稿取值。
- waterfall：unit、steps=[{label,ref,scale:1或-1,kind:total或delta}]；起终点必须勾稽。图宽有限，超过10–12项分为营业利润、税/归母两图或自绘准确SVG，不缩到不可读。
- scatter：x_label/y_label、x_scale/y_scale、points=[{label,x_ref,y_ref}]。
- 数值杜邦/证据树等自绘图：image_path和data_refs，接受本地SVG/PNG并内嵌，不接受远程脚本；必须人工核数。
- extra_data可加入有id/value/unit/formula/dependencies/source_ids的分部/行业指标，依赖必须已存在。其公式执行与勾稽需人工或单独脚本核验；同时导出到Excel/CSV底稿，不能只存于report.json。
- appendix_tables是title/columns/rows的表数组，必须覆盖核心历史、同行、公式、口径、一次性调整、同行选择、完整异常扫描状态。来源表和数值检查脚本自动追加，不能替代完整附录。
- questions是3–8个最终待验证问题；尽量给需取资料和区分假说的方法。

报告渲染器只验证结构/引用/部分数字，不自动判断数据可比性、因果、业务风险，也不能自动确认摘要1页。完成后按质量门人工复核与视觉检查。

## 4. 运行
```bash
python3 <skill-dir>/scripts/calculate_financial_ratios.py input.json --out workpapers
python3 <skill-dir>/scripts/dupont_analysis.py workpapers/analysis.json --out workpapers/dupont.json
python3 <skill-dir>/scripts/render_report.py report.json --out 公司_期间_财务研究报告.html
python3 <skill-dir>/scripts/selftest.py
```
calculate_financial_ratios只用标准库，存在openpyxl则额外输出Excel，否则完整CSV+JSON仍可复核；不为其索取不存在的权限。返回码2表示有FAIL，文件仍保留用于修正。NOT_TESTED表示缺资料不能勾稽，不是PASS。
render_report用标准库生成内嵌SVG和数据表，不联网。实际渲染使用当前环境可用浏览器/文档工具，检查图表和摘要页；不需要把报告发布成网站。
