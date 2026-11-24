# 外部平台官方集成审计（2026-11-17）

本文件回答两个问题：PRD 提到的每个数据平台有没有**官方** Codex skill 或 MCP；本机到底装了什么。原则是只安装平台官方发布的集成，不用社区 MCP 冒充官方。

## 1. 审计结论

| 平台 | 官方 Codex skill | 官方 MCP | 本机状态 | 认证 |
|---|---|---|---|---|
| CoinGecko | `coingecko` | `coingecko` | 已装 | Demo/Pro key；可 keyless 受限 |
| Binance | `binance` | `binance` | 已装；`binance-cli` 2.3.0 | OAuth；CLI 另需 key |
| OKX | `okx-cex-market` 等 | `okx`（market/read-only） | 已装 | 公共行情免 key |
| Bybit | 无独立 skill | `bybit` | 已装 | 公共行情免 key |
| CoinMarketCap | `cmc-mcp` 等 | `coinmarketcap` | 已装 | `CMC_MCP_API_KEY` |
| DefiLlama | `defi-data` 等 | `defillama` | 已装 | 订阅 + OAuth |
| Tokenomist | 7 个 `tokenomist-*` | 无官方 MCP | skill + CLI 已装 | `TOKENOMIST_API_KEY` |
| Glassnode | 无官方 skill | `glassnode` | 已装 | 公共 30 天；key 解锁完整历史 |
| Etherscan | `etherscan`、`etherscan-flow` | `etherscan` | 已装 | `ETHERSCAN_API_KEY` |
| Gate | `gate-news-listing`、`gate-news-intel`、`gate-info-*` | `gate-info`、`gate-news` | 已装（公共只读） | 无需 key |
| CryptoPanic | 未发现官方集成 | 未发现官方 MCP | 直连 API | `CRYPTOPANIC_API_KEY` |
| FRED | 未发现官方集成 | 未发现官方 MCP | 直连 API | `FRED_API_KEY` |
| Federal Reserve | 未发现官方集成 | 未发现官方 MCP | 直连网页/数据下载 | 通常免 key |
| BLS | 未发现官方集成 | 未发现官方 MCP | 直连 API | key 可选，提高限额 |
| Trading Economics | 未发现官方集成 | 未发现官方 MCP | 直连 API | 付费 key |
| SEC EDGAR | 未发现官方集成 | 未发现官方 MCP | 直连 API | 合规 User-Agent |
| CFTC | 未发现官方集成 | 未发现官方 MCP | 直连报告 | 通常免 key |
| U.S. Treasury | 未发现官方集成 | 未发现官方 MCP | 直连 FiscalData API | 通常免 key |
| CoinDesk / The Block / Blockworks | 未发现官方集成 | 未发现官方 MCP | 官方 RSS | 免 key |
| X | 未发现官方集成 | 未发现官方 MCP | 直连 API | `X_BEARER_TOKEN` |
| Reddit | 未发现官方集成 | 未发现官方 MCP | 直连 API | OAuth |

## 2. 已安装的核心依赖

### CoinGecko

- 官方 Codex 文档：https://docs.coingecko.com/ai-integration/openai-codex#python
- 官方 MCP 文档：https://docs.coingecko.com/ai-integration/mcp-server
- 官方 skill 仓库：https://github.com/coingecko/skills
- 安装：

```bash
npx skills add coingecko/skills --skill coingecko --agent codex --global --copy --yes
codex mcp add coingecko -- npx -y @coingecko/coingecko-mcp@latest
```

- 本机 MCP 使用 `COINGECKO_ENVIRONMENT=demo`；这是 npm 包的默认 Pro 模式之外的必要设置。
- 申请 key：打开 https://www.coingecko.com/en/developers/dashboard → 登录 → 创建 Demo API Key → 写入 `COINGECKO_DEMO_API_KEY` → 重启 Codex。
- 付费 Pro：https://www.coingecko.com/en/api/pricing ，使用 `COINGECKO_PRO_API_KEY` 并把环境改为 `pro`。

### Binance

- 官方 skill 仓库：https://github.com/binance/binance-skills-hub
- Agentic MCP：https://agent.binance.com/mcp/agentic
- API 管理：https://www.binance.com/en/my/settings/api-management
- 安装：

```bash
npx skills add https://github.com/binance/binance-skills-hub --skill binance --agent codex --global --copy --yes
codex mcp add binance --url https://agent.binance.com/mcp/agentic
codex mcp login binance
```

- OAuth：运行 `codex mcp login binance`，在浏览器完成授权；仅公共行情也应先确认 MCP 可用。
- CLI 已安装官方 release `2.3.0`：在 API 管理页创建只读 key，开启 IP 白名单，设置 `BINANCE_API_KEY` 与 `BINANCE_SECRET_KEY`。不要使用 npm 上旧的 `1.3.0`。

### OKX

- 官方 skills：https://github.com/okx/agent-skills
- API 管理：https://www.okx.com/account/my-api
- 安装：

```bash
npm install -g @okx_ai/okx-trade-cli@latest
npx skills add okx/agent-skills --skill okx-cex-market okx-cex-auth okx-sentiment-tracker --agent codex --global --copy --yes
codex mcp add okx -- npx -y @okx_ai/okx-trade-mcp@latest --modules market --read-only
```

- 公共行情免 key；账户/情绪需要 `okx auth login` 或只读 API key。
- 本机 MCP 固定 `--modules market --read-only`，不暴露下单能力。

### Bybit

- 官方仓库：https://github.com/bybit-exchange/trading-mcp
- API 管理：https://www.bybit.com/app/user/api-management
- 安装：

```bash
codex mcp add bybit -- npx -y bybit-official-trading-server@latest
```

- 公共行情免 key；账户数据需要只读 key，设置 `BYBIT_API_KEY`、`BYBIT_API_SECRET`，并开启 IP 白名单。

### CoinMarketCap

- 官方 skills：https://github.com/OpenCMC/skills-for-ai-agents-by-CoinMarketCap
- MCP：https://mcp.coinmarketcap.com/mcp
- Key 入口：https://pro.coinmarketcap.com/login
- 安装：

```bash
npx skills add coinmarketcap-official/skills-for-ai-agents-by-CoinMarketCap --skill cmc-mcp crypto-research market-report cmc-api-crypto cmc-api-market --agent codex --global --copy --yes
codex mcp add coinmarketcap --url https://mcp.coinmarketcap.com/mcp
```

- MCP 请求头 `X-CMC-MCP-API-KEY` 映射到 `CMC_MCP_API_KEY`。
- 申请：登录 CMC Pro → API/Developer 页面 → 创建 key → 写入环境变量 → 重启 Codex。

### DefiLlama

- 官方 skills：https://github.com/DefiLlama/defillama-skills
- MCP：https://mcp.defillama.com/mcp
- 订阅：https://defillama.com/subscribe
- 安装：

```bash
npx skills add DefiLlama/defillama-skills --skill defi-data token-research risk-assessment protocol-deep-dive flows-and-events market-analysis --agent codex --global --copy --yes
codex mcp add defillama --url https://mcp.defillama.com/mcp
codex mcp login defillama
```

- 先订阅/激活 API 计划，再执行 OAuth；免费网页抓取不能冒充同等级 API 数据。

### Tokenomist

- 官网：https://tokenomist.ai
- 文档：https://docs.tokenomist.ai
- 官方 CLI/skills：https://github.com/tokenomist-ai/tokenomist-cli
- 安装：

```bash
npm install -g @tokenomist-ai/tokenomist-cli@latest
npx skills add tokenomist-ai/tokenomist-cli --agent codex --global --copy --yes
tok auth login
```

- 也可设置 `TOKENOMIST_API_KEY`；key 文件不要读取或打印完整内容。

### Glassnode

- 官方 MCP 文档：https://docs.glassnode.com/integrations-and-tools/glassnode-mcp-server.md
- Key：https://studio.glassnode.com/settings/api
- 安装：

```bash
codex mcp add glassnode --url https://mcp.glassnode.com
```

- 公共模式可用，但最多返回最近 30 天；需要完整历史时创建 key，并配置 `X-Api-Key` 请求头映射到 `GLASSNODE_API_KEY`。
- 公共与认证模式只能二选一，不要同时注册两个 `glassnode` MCP。

### Etherscan

- 官方 skills：https://github.com/etherscan/skills
- AI/MCP 文档：https://docs.etherscan.io/ai/mcp.md
- Key：https://etherscan.io/myapikey
- 安装：

```bash
npx skills add etherscan/skills --skill etherscan etherscan-flow --agent codex --global --copy --yes
codex mcp add etherscan --url https://mcp.etherscan.io/mcp --bearer-token-env-var ETHERSCAN_API_KEY
```

- 申请：Etherscan 登录 → API Keys → Add → 复制 key → 写入 `ETHERSCAN_API_KEY` → 重启 Codex。
- MCP 使用 Bearer 认证；本 skill 只做只读查询，不提交验证、不广播交易。

### Gate

- 官方 skills：https://github.com/gate/gate-skills
- 官方 Info MCP：https://api.gatemcp.ai/mcp/info
- 官方 News MCP：https://api.gatemcp.ai/mcp/news
- 安装：

```bash
npx skills add gate/gate-skills --skill gate-news-listing gate-news-intel gate-info-marketoverview gate-info-coinanalysis gate-info-trendanalysis gate-info-riskcheck --agent codex --global --copy --yes
codex mcp add gate-info --url https://api.gatemcp.ai/mcp/info
codex mcp add gate-news --url https://api.gatemcp.ai/mcp/news
```

- 已安装的 6 个只读 skill：`gate-news-listing`、`gate-news-intel`、`gate-info-marketoverview`、`gate-info-coinanalysis`、`gate-info-trendanalysis`、`gate-info-riskcheck`。
- 只注册公共 Info/News 端点，不安装 Gate CEX 交易、资产、子账户、理财、机器人或钱包端点；无需 API key，不需要 OAuth。
- `gate-news-listing` 用于交易所公告、上币/下架与维护事件；它不能替代币安/OKX/Bybit 各自公告页。
- `gate-cli` 是官方 primary Info/News skill 的增强路径；本机未把它设为硬依赖，MCP 公共只读端点已可独立工作。

## 3. 官方 API/RSS 直连平台

这些平台没有找到官方 Codex skill/MCP。不要为了“看起来齐全”而安装来源不明的社区包；报告里注明“直连 API”。

### CryptoPanic

- API 入口：https://cryptopanic.com/developers/api/
- 步骤：注册账号 → 进入 Developers/API → 申请 token → 写入 `CRYPTOPANIC_API_KEY`。
- 用途：新闻聚合与情绪；同一事件的多条转载必须先去重。

### FRED

- API Key：https://fred.stlouisfed.org/docs/api/api_key.html
- 步骤：注册 FRED 账号 → Request API Key → 填写用途 → 收到 key 后写入 `FRED_API_KEY`。
- 用途：利率、货币供应、通胀与就业等宏观序列。

### Federal Reserve

- 数据入口：https://www.federalreserve.gov/data.htm
- 通常无需 key；优先使用官方数据下载/发布页，并记录发布日期与数据截止日期。

### U.S. Bureau of Labor Statistics

- API：https://www.bls.gov/developers/home.htm
- 步骤：可直接调用 v1；注册后可申请 `BLS_API_KEY` 提高限额，写入同名环境变量。
- 用途：CPI、PPI、非农、失业率。

### Trading Economics

- API：https://tradingeconomics.com/api/
- 步骤：注册/登录 → 选择 API 计划 → 获取 key → 写入 `TRADING_ECONOMICS_API_KEY`。
- 用途：全球宏观日历与指标；付费端点权限以订阅为准。

### SEC EDGAR

- API 文档：https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- 无需 key；必须设置可识别的合规 User-Agent，并遵守速率限制。
- 用途：ETF、上市公司披露、监管文件与持仓。

### CFTC

- 市场报告：https://www.cftc.gov/MarketReports/index.htm
- 通常无需 key；用途包括 COT 持仓、监管报告与市场结构。

### U.S. Treasury

- FiscalData API：https://fiscaldata.treasury.gov/api-documentation/
- 通常无需 key；用途包括国债收益率、财政收支与 TGA。

### 加密新闻 RSS

- CoinDesk：https://www.coindesk.com/arc/outboundfeeds/rss/
- The Block：https://www.theblock.co/rss.xml
- Blockworks：https://blockworks.co/feed
- RSS 免 key；必须记录发布时间、抓取时间与原文链接，不能把旧闻当突发利好。

### X

- 开发者入口：https://developer.x.com/
- 步骤：注册开发者账号 → 创建 Project/App → 获取 Bearer Token → 写入 `X_BEARER_TOKEN`。
- 用途仅限公开帖文与情绪；不要把 X 热度当作事实确认。

### Reddit

- API 文档：https://www.reddit.com/dev/api/
- 步骤：创建 Reddit App → 获取 client id/secret → 完成 OAuth → 写入 `REDDIT_CLIENT_ID` 等环境变量。
- 用途：社区情绪与讨论热度；必须去重并与官方公告交叉验证。

## 4. 未采用或未被 PRD 引用的平台

| 平台 | 审计结果 | 处理 |
|---|---|---|
| Coinbase | 官方仓库主要是 Payments MCP 与 agentic-wallet skills，不是市场研究数据集成 | 不安装；PRD 未引用 |
| Coinglass | 未发现官方 Codex skill/MCP；PRD 未引用 | 不安装；如用户明确要求，先查官方 API 文档再直连 |
| Dune / Nansen / Arkham / Messari | PRD 未引用 | 不安装；不使用社区包替代官方数据 |

如果后续 PRD 新增这些平台，先补官方文档审计，再决定是否安装；不得先装社区 MCP 再倒推合法性。

## 5. 安装顺序与验证

推荐顺序：

1. 先装官方 skill + MCP。
2. 再配置 API key/OAuth。
3. 运行 `scripts/check_dependencies.py --json`，确认没有 `missing_install`。
4. 运行 `--strict --json`，确认所有必需认证完成；strict 失败时不要开始完整交易决策。

```bash
python3 "$HOME/.agents/skills/three-sides-three-thoughts-trading/scripts/check_dependencies.py" --json
python3 "$HOME/.agents/skills/three-sides-three-thoughts-trading/scripts/check_dependencies.py" --strict --json
```

门禁只检查名称、路径和环境变量是否存在，不读取或打印密钥值。
