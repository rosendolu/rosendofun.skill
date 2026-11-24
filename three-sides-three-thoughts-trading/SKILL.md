---
name: three-sides-three-thoughts-trading
description: Use for crypto trading research and risk-controlled decision support based on the Three Sides and Three Thoughts framework. Covers BTC, ETH, ICP and similar assets across spot and USDT perpetual futures; requires the installed CoinGecko, Binance, OKX, Bybit, CoinMarketCap, DefiLlama, Glassnode, Etherscan, Tokenomist and Gate dependencies before full analysis. Do not use for automatic order execution, custody, or promises of returns.
license: MIT
metadata:
  display-name: 三面三思六位交易战法
  short-description: 三面三思六维交易研究与风险决策
  version: 1.0.0
  source: 三面三思交易法 PRD
  author: local
---

# 三面三思六位交易战法

把基本面、消息面、技术面（三面）与居安思危、思变、思退（三思）合并为可复核的交易研究流程。这里把 PRD 中的“六位”按六维评分体系执行。产品定位是研究与决策支持，不是自动交易系统。

技术目录名使用 `three-sides-three-thoughts-trading`（Codex skill 规范要求小写连字符）；对外显示名与产品名统一为“三面三思六位交易战法”。

## 0. 依赖门禁（硬性，先于任何分析）

每次开始分析前，先运行：

```bash
python3 "$HOME/.agents/skills/three-sides-three-thoughts-trading/scripts/check_dependencies.py" --json
```

如果当前 skill 不在该路径，使用本 `SKILL.md` 所在目录下的 `scripts/check_dependencies.py`。

规则：

1. 退出码非 0，或输出 `status` 为 `blocked` 时，**不要开始行情分析、评分或交易建议**。
2. 向用户列出缺失的 MCP、skill、CLI、API Key 或 OAuth 状态，并给出 `references/data-sources.md` 中对应的安装命令和申请链接。
3. 只有门禁通过后才读取行情；不要用记忆中的价格、市值、资金费率或新闻替代实时数据。
4. 缺少关键认证时，只能进入用户明确接受的“受限研究模式”，并必须把缺失项写进数据质量与结论限制；不能输出可执行开仓结论。
5. 不要自动下单、不要索取私钥、不要连接真实交易账户执行写操作。

需要真实资金或开仓结论时，改用严格门禁；它会把缺失 API Key/OAuth 也视为阻塞：

```bash
python3 "$HOME/.agents/skills/three-sides-three-thoughts-trading/scripts/check_dependencies.py" --strict --json
```

必需依赖：

| 能力 | MCP | 官方 skill | 认证 |
|---|---|---|---|
| 市场与链上交叉验证 | `coingecko` | `coingecko` | Demo/Pro API Key，或 keyless 受限模式 |
| 交易所行情与合约数据 | `binance`、`okx`、`bybit` | `binance`、`okx-cex-market` | Binance OAuth；OKX/Bybit 公共行情可免 key |
| 市值、排名、情绪与新闻交叉验证 | `coinmarketcap` | `cmc-mcp` | `CMC_MCP_API_KEY` |
| TVL、协议收入、解锁与 ETF 流 | `defillama` | `defi-data`、`token-research` | DefiLlama 订阅 + OAuth |
| 链上活跃度、交易所余额、长期持有者行为 | `glassnode` | 无官方 skill | 公共模式仅 30 天；完整历史用 `GLASSNODE_API_KEY` |
| 交易、合约、地址资金流与事件追踪 | `etherscan` | `etherscan`、`etherscan-flow` | `ETHERSCAN_API_KEY`（Bearer） |
| 交易所公告、上币/下架、新闻与情绪 | `gate-info`、`gate-news` | `gate-news-listing`、`gate-news-intel`、`gate-info-*` | 公共只读，无需 key |

安装、API Key 申请与更新方式见 `references/data-sources.md`；每个平台的官方来源审计、未采用平台和完整申请流程见 `references/platform-audit.md`。依赖检查脚本会检查本机状态，不打印任何密钥值。

宏观、新闻与社交平台（CryptoPanic、FRED、BLS、Trading Economics、SEC EDGAR、CFTC、Treasury、新闻 RSS、X、Reddit）未发现官方 Codex skill/MCP，按官方 REST/RSS/网页直连，并在报告中标注“直连 API”。不要把社区 MCP 说成官方集成。

## 1. 适用范围与安全边界

- 首版重点：BTC、ETH、ICP；现货与 USDT 永续合约研究。
- 输出可以是 `可以评估开仓`、`谨慎交易`、`优先观望`、`不考虑做多`、`禁止新增风险`，但不能把评分当作下单指令。
- 强平价、保证金率、手续费、资金费率和可成交深度必须以交易所账户与合约规则为准。LLM 不得自行推导强平价。
- 没有退出方案、没有强平安全距离、数据异常或原逻辑失效时，硬性风控优先于任何高分。
- 任何“看多”结论必须同时给出看空理由和失效条件。

## 2. 标准工作流

### 2.1 明确任务模式

先识别用户要的是哪一种：

- **研究模式**：只做三面信息与风险解释，不要求账户资金、杠杆或开仓计划。
- **交易决策模式**：需要标的、交易所、市场类型、周期、账户权益、单笔风险比例、杠杆上限、入场与止损假设。

交易决策模式缺少账户权益、风险预算、入场价或止损价时，先追问；不得编造账户规模或强平价。可以先用模拟参数演示公式，但必须标注“模拟数据”。

### 2.2 三面数据采集

并行获取，避免单指标决策：

1. **基本面**：CoinGecko/CMC 的市值、FDV、流通量、供应量；DefiLlama 的 TVL、费用、收入、协议事件、ETF/机构流；Tokenomist 等解锁数据（有 key 时）。
2. **消息面**：CoinGecko/CMC 新闻、OKX 情绪与新闻、CryptoPanic（有 key 时）；官方公告、监管与宏观日历优先于二手转载。
3. **技术面**：Binance/OKX/Bybit 的 OHLCV、订单簿、OI、资金费率、多空比、爆仓与基差；按 1D、4H、1H 为主，15m/5m 只用于执行。

数据规则：

- 每个关键数字附来源、数据时间、抓取时间、延迟、是否交叉验证、是否缺失或异常。
- 不同交易所、现货与合约的成交量不能直接相加或混用。
- 同一事件的多条转载先去重，再作为一条事件评分。
- 价格、成交量、持仓量、资金费率等事实不能凭记忆补全；拿不到就明确写“不可用”。

### 2.3 三思与硬性风控

- **居安思危**：识别市场、杠杆、流动性、消息、资金、资产六类风险；至少模拟正常涨跌、5% 暴跌、10%–20% 极端下跌。
- **思变**：比较上次快照与当前状态，判断原交易逻辑是否仍成立；变化分 Level 1/2/3。
- **思退**：开仓前必须有入场、止损、止盈、仓位、杠杆、最大亏损、强平价、逻辑失效条件；止损必须早于强平并留有安全距离。

确定性计算统一交给脚本，不要让 LLM 心算：

```bash
python3 "$HOME/.agents/skills/three-sides-three-thoughts-trading/scripts/score_decision.py" --input-json /tmp/three-sides-input.json --json
```

输入字段、决策边界和硬门槛见 `references/methodology.md` 与 `references/output-contract.md`。

## 3. 评分与决策

机会评分（越高越好）：

```text
O = 0.30F + 0.25N + 0.45T
```

风险评分（越高风险越大）：

```text
R = 0.35W + 0.30V + 0.35E
```

其中 F/N/T 分别为基本面、消息面、技术面；W/V/E 分别为居安思危、思变、思退。六个维度均为 0–100。

PRD 决策表：

| 机会 O | 风险 R | 决策 |
|---|---|---|
| 80–100 | 0–30 | 可以评估开仓 |
| 60–79 | 0–40 | 谨慎交易 |
| 40–59 | 任意 | 优先观望 |
| 0–39 | 任意 | 不考虑做多 |
| 任意 | 70–100 | 风险优先，禁止新增风险 |

PRD 未覆盖组合按保守原则处理：`O >= 80` 且 `31 <= R <= 69` 时，默认“谨慎交易”并明确说明该区间未被原表覆盖；其余未覆盖组合优先观望。硬性门槛永远高于评分。

## 4. 三个硬性门槛

以下任一条件不满足，结论必须是“禁止开仓”或“重新评估”，不能因为机会评分高而放行：

1. 思退方案缺失：没有止损、仓位、最大亏损、强平风险或逻辑失效条件。
2. 强平安全距离不足：止损不早于强平价，或安全距离不足；必须以交易所实际规则与账户数据复核。
3. 数据或逻辑失效：重大消息真实性无法确认、交易所数据异常、原交易逻辑失效时，分别降低权限、暂停依赖该数据的决策或触发重新评估。

## 5. 最终输出

先给结论，再给证据。完整报告至少包含：

- 标的、市场、交易所、分析时间、数据截止时间。
- 三面评分与判断，三思评分与判断。
- 机会评分、风险评分、最终决策、硬门槛状态。
- 看多理由与看空理由，以及“看多逻辑是否足以覆盖看空风险”的回答。
- 交易计划（仅交易决策模式）：入场、止损、止盈、仓位、杠杆、保证金、强平安全距离、R 倍数。
- 数据质量：来源、时间、延迟、交叉验证、缺失、异常。
- 失效条件与下次复核触发条件。

完整 JSON/Markdown 模板见 `references/output-contract.md`。如果数据不足，输出“数据不足，暂不决策”，不要用看似精确的数字填空。

## 6. 参考文件

- `references/methodology.md`：三面三思细节、评分锚点、新闻公式、仓位与强平规则。
- `references/data-sources.md`：平台清单、官方 skill/MCP、安装命令、API Key 申请链接与 OAuth 流程。
- `references/platform-audit.md`：逐平台官方集成审计、已安装/未安装结论、Key 申请步骤与验证顺序。
- `references/output-contract.md`：报告结构、JSON 字段、硬门槛与示例。
- `scripts/check_dependencies.py`：开头的依赖门禁。
- `scripts/score_decision.py`：确定性评分、决策与仓位计算。

