# 外部平台、官方 Skill/MCP、安装与 API Key

本文件是依赖门禁的安装参考。状态以本机 `scripts/check_dependencies.py` 的实时输出为准；下表记录 2026-11-17 已完成的本机安装与其认证入口。逐平台的官方来源审计、未采用平台与完整 Key 申请流程另见 `references/platform-audit.md`。

## 1. 已安装的核心依赖

| 平台 | 官方 skill | MCP | 本机状态 | 认证 |
|---|---|---|---|---|
| CoinGecko | `coingecko` | `coingecko`（stdio，npm） | skill + MCP 已装 | Demo/Pro API Key；keyless 受限 |
| Binance | `binance` | `binance`（remote） | skill + MCP 已注册；`binance-cli` 2.3.0 已装 | OAuth；CLI 另需 API Key |
| OKX | `okx-cex-market`、`okx-cex-auth`、`okx-sentiment-tracker` | `okx`（stdio，read-only market） | skill + CLI + MCP 已装 | 公共行情免 key；账户/情绪需 OAuth 或 API Key |
| Bybit | 无官方独立 skill | `bybit`（stdio，官方包） | MCP 已装 | 公共行情免 key；账户需 API Key |
| CoinMarketCap | `cmc-mcp`、`crypto-research`、`market-report`、`cmc-api-*` | `coinmarketcap`（remote） | skill + MCP 已装 | `CMC_MCP_API_KEY` |
| DefiLlama | `defi-data`、`token-research`、`risk-assessment` 等 | `defillama`（remote） | skill + MCP 已装 | 订阅 + OAuth |
| Tokenomist | 7 个 `tokenomist-*` skill | 无官方 MCP；官方 CLI `tok` | skill + CLI 已装 | `TOKENOMIST_API_KEY` |
| Glassnode | 无官方 skill | `glassnode`（remote，官方 MCP） | MCP 已装 | 公共模式仅 30 天；完整历史需 `GLASSNODE_API_KEY` |
| Etherscan | `etherscan`、`etherscan-flow` | `etherscan`（remote，官方 MCP） | skill + MCP 已装 | `ETHERSCAN_API_KEY`（Bearer） |
| Gate | `gate-news-listing`、`gate-news-intel`、`gate-info-*` | `gate-info`、`gate-news`（remote，官方 MCP） | skill + MCP 已装 | 公共只读，无需 key |

## 2. CoinGecko（已安装）

官方资料：

- Codex 集成文档：https://docs.coingecko.com/ai-integration/openai-codex#python
- MCP 文档：https://docs.coingecko.com/ai-integration/mcp-server
- Agent skill：https://docs.coingecko.com/ai-integration/agent-skill
- 官方 skill 仓库：https://github.com/coingecko/skills

安装：

```bash
npx skills add coingecko/skills --skill coingecko --agent codex --global --copy --yes
codex mcp add coingecko -- npx -y @coingecko/coingecko-mcp@latest
```

本机 MCP 配置使用 `env_vars` 透传 `COINGECKO_DEMO_API_KEY`、`COINGECKO_PRO_API_KEY`，并默认 `COINGECKO_ENVIRONMENT=demo`。Code Mode 需要 Deno；本机已检测到 Deno。

申请 Demo Key：

1. 打开 https://www.coingecko.com/en/developers/dashboard 并登录/注册。
2. 在 Developer Dashboard 创建 Demo API Key。
3. 将 key 放入环境变量 `COINGECKO_DEMO_API_KEY`，不要把 key 写进 skill 或聊天。
4. 重启 Codex，使 MCP 的子进程读取到新环境变量。

付费计划：https://www.coingecko.com/en/api/pricing 。Pro key 使用 `COINGECKO_PRO_API_KEY`，并把 `COINGECKO_ENVIRONMENT` 改为 `pro`。

Keyless 限制：可按 IP 限频，只适合少量查询；不能调用部分 onchain 端点，不能作为完整六维报告的可靠唯一来源。

## 3. Binance（已安装）

官方资料：

- Skills Hub：https://github.com/binance/binance-skills-hub
- Binance Agentic MCP：https://agent.binance.com/mcp/agentic
- API 管理：https://www.binance.com/en/my/settings/api-management
- API 文档：https://developers.binance.com/

安装：

```bash
npx skills add https://github.com/binance/binance-skills-hub --skill binance --agent codex --global --copy --yes
codex mcp add binance --url https://agent.binance.com/mcp/agentic
```

认证：

```bash
codex mcp login binance
```

如果使用 `binance-cli`（官方 skill 的 CLI 路径）：

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/binance/binance-cli/releases/latest/download/binance-cli-installer.sh \
  | sh
binance-cli --version
```

1. 在 API 管理页创建 API Key，建议只开启读取权限并设置 IP 白名单。
2. 设置 `BINANCE_API_KEY` 与 `BINANCE_SECRET_KEY`；测试网使用 `BINANCE_API_ENV=testnet`。
3. 或运行 `binance-cli profile create --name <name> --api-key <key> --api-secret <secret> --env prod`。

`binance-cli` 必须是官方 release 的 `>=2.0.0`；npm 当前的 `1.3.0` 不满足官方 skill 的版本要求，不要用它替代。本 skill 以只读行情与风控研究为主，不需要提现或交易权限。若本机没有 `binance-cli`，MCP 仍可用于行情；CLI skill 的完整命令需要该二进制。

## 4. OKX（已安装）

官方资料：

- 官方 skills：https://github.com/okx/agent-skills
- API 管理：https://www.okx.com/account/my-api
- API 文档：https://www.okx.com/docs-v5/en/

安装：

```bash
npm install -g @okx_ai/okx-trade-cli@latest
npx skills add okx/agent-skills --skill okx-cex-market okx-cex-auth --agent codex --global --copy --yes
codex mcp add okx -- npx -y @okx_ai/okx-trade-mcp@latest --modules market --read-only
```

本机 MCP 限定 `--modules market --read-only`，不会暴露下单、账户或机器人写操作。

认证：

- 公共行情：`okx market ticker BTC-USDT --json` 不需要 key。
- OAuth：按 `okx-cex-auth` skill 执行 `okx auth login`，或使用 `okx auth status --json` 检查。
- API Key：在 API 管理页创建 read-only key，记录 API Key、Secret、Passphrase；然后运行 `okx config init` 或写入 `~/.okx/config.toml`。

## 5. Bybit（已安装 MCP）

官方资料：

- 官方仓库：https://github.com/bybit-exchange/trading-mcp
- API 管理：https://www.bybit.com/app/user/api-management
- API 文档：https://bybit-exchange.github.io/docs/v5/intro

安装：

```bash
codex mcp add bybit -- npx -y bybit-official-trading-server@latest
```

认证：

- 23 个公共行情工具无需 API Key。
- 账户、仓位、交易等工具需要 read-only API Key：
  1. 在 API 管理页创建“系统生成”的 API Key。
  2. 只开启读取权限并设置 IP 白名单。
  3. 设置 `BYBIT_API_KEY` 与 `BYBIT_API_SECRET`；RSA 模式使用 `BYBIT_API_PRIVATE_KEY_PATH`。
  4. 测试网设置 `BYBIT_TESTNET=true`。

本 skill 只要求公共行情可用；不要为了研究开启交易或提现权限。

## 6. CoinMarketCap（已安装）

官方资料：

- 官方 skills：https://github.com/OpenCMC/skills-for-ai-agents-by-CoinMarketCap
- MCP：https://mcp.coinmarketcap.com/mcp
- API Key 入口：https://pro.coinmarketcap.com/login
- API 文档：https://coinmarketcap.com/api/documentation/v1/

安装：

```bash
npx skills add coinmarketcap-official/skills-for-ai-agents-by-CoinMarketCap --skill cmc-mcp crypto-research market-report cmc-api-crypto cmc-api-market --agent codex --global --copy --yes
codex mcp add coinmarketcap --url https://mcp.coinmarketcap.com/mcp
```

CMC MCP 通过请求头 `X-CMC-MCP-API-KEY` 认证。本机配置用 `env_http_headers` 将该请求头映射到环境变量 `CMC_MCP_API_KEY`。

申请步骤：

1. 打开 https://pro.coinmarketcap.com/login ，注册或登录。
2. 进入 API / Developer 页面创建 API Key。
3. 将 key 放入 `CMC_MCP_API_KEY`。
4. 重启 Codex；不要将 key 粘贴到聊天或写入报告。

免费额度与端点权限以 CMC 控制台为准；如果 key 缺失，CMC 只能作为“未验证”来源，不能用它伪装交叉验证。

## 7. DefiLlama（已安装）

官方资料：

- 官方 skills：https://github.com/DefiLlama/defillama-skills
- MCP：https://mcp.defillama.com/mcp
- 订阅入口：https://defillama.com/subscribe
- API 文档：https://defillama.com/docs/api

安装：

```bash
npx skills add DefiLlama/defillama-skills --skill defi-data token-research risk-assessment protocol-deep-dive flows-and-events market-analysis --agent codex --global --copy --yes
codex mcp add defillama --url https://mcp.defillama.com/mcp
```

认证：

1. 在 https://defillama.com/subscribe 购买/激活 API 计划。
2. 运行 `codex mcp login defillama`，按浏览器提示登录并授权。
3. 不需要 API key 或环境变量；OAuth 会话由 Codex 保存。

DefiLlama 订阅是 TVL、协议收入、ETF 流、解锁与 institutional 数据的主要来源；未订阅时不要把免费网页抓取当成同等级 API 数据。

## 8. Tokenomist（已安装 CLI + skills）

官方资料：

- 官网/API Key：https://tokenomist.ai
- 文档：https://docs.tokenomist.ai
- 官方 CLI 与 skills：https://github.com/tokenomist-ai/tokenomist-cli

安装：

```bash
npm install -g @tokenomist-ai/tokenomist-cli@latest
npx skills add tokenomist-ai/tokenomist-cli --agent codex --global --copy --yes
```

认证：

```bash
tok auth login
tok auth status
```

也可设置 `TOKENOMIST_API_KEY`。key 存储在 `~/.tokenomist/config.json`（0600）时不要读取或打印完整内容。

常用只读命令：

```bash
tok token list --output json
tok unlock upcoming --output json
tok unlock events <symbol> --output json
tok emission daily <symbol> --output json
tok allocation detail <symbol> --output json
tok pit allocation <symbol> --as-of <date> --output json
```

## 9. Glassnode（已安装官方 MCP）

官方资料：

- MCP 文档：https://docs.glassnode.com/integrations-and-tools/glassnode-mcp-server.md
- API 文档：https://docs.glassnode.com/basic-api/endpoints
- 指标目录：https://docs.glassnode.com/data/metric-catalog
- API Key：https://studio.glassnode.com/settings/api

安装（本机采用公共只读模式）：

```bash
codex mcp add glassnode --url https://mcp.glassnode.com
```

认证与限制：

1. 公共模式不需要 key，但单次查询最多返回最近 30 天，适合当前快照与短期交叉验证。
2. 需要完整历史时，在 https://studio.glassnode.com/settings/api 创建 API Key。
3. 将 key 放入 `GLASSNODE_API_KEY`，并在 Codex `config.toml` 中为现有 `glassnode` 条目增加：

```toml
env_http_headers = { "X-Api-Key" = "GLASSNODE_API_KEY" }
```

4. 重启 Codex。公共模式与认证模式只能保留一个 `glassnode` 配置，不要同时注册两个同名 MCP。
5. API 调用会消耗 Glassnode credits；批量取数优先用 `fetch_bulk_metrics`，不要对同一指标逐资产重复调用。

本 skill 只使用 Glassnode 的只读指标与元数据能力；不要用其输出替代交易所强平价或账户风险数据。

## 10. Etherscan（已安装官方 skills + MCP）

官方资料：

- 官方 skills：https://github.com/etherscan/skills
- AI/MCP 文档：https://docs.etherscan.io/ai/mcp.md
- API 文档：https://docs.etherscan.io/
- API Key：https://etherscan.io/myapikey

安装：

```bash
npx skills add etherscan/skills --skill etherscan etherscan-flow --agent codex --global --copy --yes
codex mcp add etherscan --url https://mcp.etherscan.io/mcp --bearer-token-env-var ETHERSCAN_API_KEY
```

如果 `npx skills add` 因 GitHub `git clone` 超时失败，可用官方仓库 tarball 兜底，再复制完整 skill 目录：

```bash
curl -L -o /tmp/etherscan-skills.tar.gz https://codeload.github.com/etherscan/skills/tar.gz/refs/heads/main
mkdir -p /tmp/etherscan-skills
tar -xzf /tmp/etherscan-skills.tar.gz -C /tmp/etherscan-skills --strip-components=1
cp -R /tmp/etherscan-skills/skills/etherscan ~/.agents/skills/
cp -R /tmp/etherscan-skills/skills/etherscan-flow ~/.agents/skills/
```

复制后运行 `npx skills list -g --json`，确认两个 skill 已注册。

认证：

1. 打开 https://etherscan.io/myapikey ，注册/登录 Etherscan 账号。
2. 进入 API Keys 页面，点击 Add，创建 key；免费 key 的速率与链支持以控制台为准。
3. 将 key 放入 `ETHERSCAN_API_KEY`，不要把 key 写进 skill、报告或聊天。
4. 重启 Codex。MCP 使用 `Authorization: Bearer <ETHERSCAN_API_KEY>`；缺失 key 时返回 401。

已安装的两个官方 skill：

- `etherscan`：在网站、API、CLI、MCP 之间选择正确入口，并校验链、分页、限额与错误。
- `etherscan-flow`：追踪地址/交易资金流，输出可复核的节点与边；适合验证交易所净流、巨鲸转账与事件资金路径。

Etherscan MCP 默认按只读使用。不要调用任何提交验证、广播交易或修改外部状态的接口；本 skill 不需要这些能力。

如果本机网络无法访问 `mcp.etherscan.io`，MCP 会超时；此时可先用官方 CLI 或 API 完成只读查询，并在报告中注明 MCP 未连通。不要把网络超时误判为 key 无效。

## 11. Gate（已安装官方 Info/News MCP 与只读 skills）

官方资料：

- 官方仓库：https://github.com/gate/gate-skills
- Info MCP：https://api.gatemcp.ai/mcp/info
- News MCP：https://api.gatemcp.ai/mcp/news
- 官方 MCP 安装器：https://github.com/gate/gate-skills/tree/master/skills/gate-mcp-installer

安装：

```bash
npx skills add gate/gate-skills --skill gate-news-listing gate-news-intel gate-info-marketoverview gate-info-coinanalysis gate-info-trendanalysis gate-info-riskcheck --agent codex --global --copy --yes
codex mcp add gate-info --url https://api.gatemcp.ai/mcp/info
codex mcp add gate-news --url https://api.gatemcp.ai/mcp/news
```

如果 `npx skills add` 因 GitHub `git clone` 超时失败，可用官方仓库 tarball 兜底，再复制选定的 skill 目录：

```bash
curl -L -o /tmp/gate-skills.tar.gz https://codeload.github.com/gate/gate-skills/tar.gz/refs/heads/master
mkdir -p /tmp/gate-skills
tar -xzf /tmp/gate-skills.tar.gz -C /tmp/gate-skills --strip-components=1
cp -R /tmp/gate-skills/skills/gate-news-listing ~/.agents/skills/
cp -R /tmp/gate-skills/skills/gate-news-intel ~/.agents/skills/
cp -R /tmp/gate-skills/skills/gate-info-marketoverview ~/.agents/skills/
cp -R /tmp/gate-skills/skills/gate-info-coinanalysis ~/.agents/skills/
cp -R /tmp/gate-skills/skills/gate-info-trendanalysis ~/.agents/skills/
cp -R /tmp/gate-skills/skills/gate-info-riskcheck ~/.agents/skills/
```

认证与边界：

1. 本机只注册 `gate-info` 与 `gate-news` 两个公共只读端点，不注册交易所账户、下单、划转或钱包端点。
2. 两个端点均无需 key；Info 提供币种、行情、K 线、链上、宏观、DeFi/CEX 指标与安全筛查，News 提供新闻、事件、社交情绪、市场异动与预测市场研究。
3. 官方 skill 的运行时规则要求先做路由预检；本 skill 只允许调用 `gate-info`/`gate-news` 中列出的只读工具。
4. 交易所公告与上币/下架优先用 `gate-news-listing`；不要把 Gate 公告当作币安/OKX/Bybit 官方公告的替代，其他交易所公告仍从各自官方 Help Center/Announcements 获取。
5. `gate-cli` 是 Gate 官方 Info/News primary skills 的增强路径，但不是本 skill 的硬依赖；未安装 CLI 时只使用已注册的 MCP 工具。

## 12. 无官方 MCP 的 PRD 数据源（REST/CLI 接入）

以下平台未发现官方 Codex skill/MCP；不要安装来源不明的社区 MCP 冒充官方。使用官方 REST API、CLI 或 RSS，并在报告中注明“直连 API”。

| 平台 | 数据 | 官方入口 / Key 流程 | 环境变量 |
|---|---|---|---|
| CryptoPanic | 新闻聚合、情绪 | https://cryptopanic.com/developers/api/ ；注册开发者账号获取 token | `CRYPTOPANIC_API_KEY` |
| FRED | 利率、货币供应、宏观指标 | https://fred.stlouisfed.org/docs/api/api_key.html ；Request API Key | `FRED_API_KEY` |
| Trading Economics | 全球宏观日历与指标 | https://tradingeconomics.com/api/ ；申请试用/付费 key | `TRADING_ECONOMICS_API_KEY` |
| BLS | CPI、就业 | https://www.bls.gov/developers/home.htm ；注册后可提高限额 | `BLS_API_KEY` |
| SEC EDGAR | filings、ETF、监管披露 | https://www.sec.gov/search-filings/edgar-application-programming-interfaces | 设置合规 User-Agent，无需 key |
| CFTC | 持仓、监管报告 | https://www.cftc.gov/MarketReports/index.htm | 通常无需 key |
| Federal Reserve | 利率决议、政策、数据 | https://www.federalreserve.gov/data.htm | 通常无需 key |
| U.S. Treasury | 财政、收益率、TGA | https://fiscaldata.treasury.gov/api-documentation/ | 通常无需 key |
| CoinDesk | 新闻 | https://www.coindesk.com/arc/outboundfeeds/rss/ | RSS，无需 key |
| The Block | 新闻 | https://www.theblock.co/rss.xml | RSS，无需 key |
| Blockworks | 新闻 | https://blockworks.co/feed | RSS，无需 key |
| X | 社交情绪 | https://developer.x.com/ | `X_BEARER_TOKEN` |
| Reddit | 社区情绪 | https://www.reddit.com/dev/api/ | OAuth / `REDDIT_CLIENT_ID` |

FRED、BLS、Treasury 等官方数据优先使用 API/RSS；如果需要网页抓取，必须遵守 robots、速率限制与 User-Agent 要求。

## 13. 凭据管理与故障处理

- 密钥只放环境变量、系统钥匙串或平台官方配置文件；不要写进 `SKILL.md`、报告、截图、日志或 git。
- MCP 的 `env_vars` 只透传环境变量名；Codex 重启后才会读取新值。
- `codex mcp list` 显示服务器存在，不等于 OAuth 已完成；Binance/DefiLlama 需显式 `codex mcp login <name>`。
- CMC 的 `X-CMC-MCP-API-KEY` 缺失时，远程 MCP 会失败；先设置 `CMC_MCP_API_KEY` 再重试。
- CoinGecko 没有 key 时可 keyless，但必须降低数据质量评级并避免高频批量调用。
- OKX/Bybit 公共行情不需要 key；账户、仓位与写操作不在本 skill 的默认范围内。
- 任何 MCP 超时、429、空结果或 schema 变化，都先记录异常并换用官方 REST 交叉验证；不要静默跳过。

## 14. 依赖检查

```bash
python3 "$HOME/.agents/skills/three-sides-three-thoughts-trading/scripts/check_dependencies.py"
```

严格模式会把缺少 API Key/OAuth 也视为阻塞：

```bash
python3 "$HOME/.agents/skills/three-sides-three-thoughts-trading/scripts/check_dependencies.py" --strict
```

脚本只报告变量是否存在，不输出密钥值。

