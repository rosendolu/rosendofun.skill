#!/usr/bin/env python3
"""Dependency gate for the three-sides-three-thoughts-trading skill.

Only reports whether names/paths exist. It never prints credential values.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


MCP_REQUIRED = [
    "coingecko",
    "binance",
    "okx",
    "bybit",
    "coinmarketcap",
    "defillama",
    "glassnode",
    "etherscan",
    "gate-info",
    "gate-news",
]

SKILL_REQUIRED = [
    "coingecko",
    "binance",
    "okx-cex-market",
    "cmc-mcp",
    "defi-data",
    "tokenomist-unlock-analysis",
    "etherscan",
    "etherscan-flow",
    "gate-news-listing",
    "gate-news-intel",
    "gate-info-marketoverview",
    "gate-info-coinanalysis",
    "gate-info-trendanalysis",
    "gate-info-riskcheck",
]

INSTALL_COMMANDS = {
    "coingecko": [
        "npx skills add coingecko/skills --skill coingecko --agent codex --global --copy --yes",
        "codex mcp add coingecko -- npx -y @coingecko/coingecko-mcp@latest",
    ],
    "binance": [
        "npx skills add https://github.com/binance/binance-skills-hub --skill binance --agent codex --global --copy --yes",
        "codex mcp add binance --url https://agent.binance.com/mcp/agentic",
        "codex mcp login binance",
    ],
    "okx": [
        "npm install -g @okx_ai/okx-trade-cli@latest",
        "npx skills add okx/agent-skills --skill okx-cex-market okx-cex-auth --agent codex --global --copy --yes",
        "codex mcp add okx -- npx -y @okx_ai/okx-trade-mcp@latest --modules market --read-only",
    ],
    "bybit": [
        "codex mcp add bybit -- npx -y bybit-official-trading-server@latest",
    ],
    "coinmarketcap": [
        "npx skills add coinmarketcap-official/skills-for-ai-agents-by-CoinMarketCap --skill cmc-mcp crypto-research market-report --agent codex --global --copy --yes",
        "codex mcp add coinmarketcap --url https://mcp.coinmarketcap.com/mcp",
        "export CMC_MCP_API_KEY=your_cmc_key",
    ],
    "defillama": [
        "npx skills add DefiLlama/defillama-skills --skill defi-data token-research risk-assessment --agent codex --global --copy --yes",
        "codex mcp add defillama --url https://mcp.defillama.com/mcp",
        "codex mcp login defillama",
    ],
    "tokenomist": [
        "npm install -g @tokenomist-ai/tokenomist-cli@latest",
        "npx skills add tokenomist-ai/tokenomist-cli --agent codex --global --copy --yes",
        "tok auth login",
    ],
    "glassnode": [
        "codex mcp add glassnode --url https://mcp.glassnode.com",
    ],
    "etherscan": [
        "npx skills add etherscan/skills --skill etherscan etherscan-flow --agent codex --global --copy --yes",
        "codex mcp add etherscan --url https://mcp.etherscan.io/mcp --bearer-token-env-var ETHERSCAN_API_KEY",
        "export ETHERSCAN_API_KEY=your_etherscan_key",
    ],
    "gate": [
        "npx skills add gate/gate-skills --skill gate-news-listing gate-news-intel gate-info-marketoverview gate-info-coinanalysis gate-info-trendanalysis gate-info-riskcheck --agent codex --global --copy --yes",
        "codex mcp add gate-info --url https://api.gatemcp.ai/mcp/info",
        "codex mcp add gate-news --url https://api.gatemcp.ai/mcp/news",
    ],
}


def skill_roots() -> list[Path]:
    roots = [Path.home() / ".agents" / "skills"]
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        roots.append(Path(codex_home) / "skills")
    roots.append(Path.home() / ".codex" / "skills")
    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        if root not in seen:
            seen.add(root)
            unique.append(root)
    return unique


def find_skill(name: str) -> str | None:
    for root in skill_roots():
        candidate = root / name / "SKILL.md"
        if candidate.is_file():
            return str(candidate)
    return None


def mcp_snapshot() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["codex", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc), "lines": {}}

    lines: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        name = stripped.split()[0]
        if name in MCP_REQUIRED:
            lines[name] = stripped
    return {"error": None, "lines": lines}


def mcp_present(mcp: dict[str, Any], name: str) -> bool:
    return name in mcp.get("lines", {})


def mcp_auth_note(mcp: dict[str, Any], name: str) -> str | None:
    line = mcp.get("lines", {}).get(name)
    if not line:
        return None
    if name in {"glassnode", "gate-info", "gate-news"}:
        return None
    if name == "coinmarketcap" and ("Not logged in" in line or "Unknown" in line):
        return "CoinMarketCap 使用 API Key 认证；设置 `CMC_MCP_API_KEY` 后重启 Codex，不需要 OAuth。"
    if name == "defillama" and ("Not logged in" in line or "Unknown" in line):
        return "DefiLlama 需要 API 订阅并完成 OAuth；先订阅，再运行 `codex mcp login defillama`。"
    if name == "etherscan":
        return None
    if "Not logged in" in line:
        return "OAuth 尚未登录；运行 `codex mcp login %s`" % name
    if "Unknown" in line:
        return "认证状态未知；检查 API Key/环境变量后重启 Codex"
    return None


def env_present(*names: str) -> bool:
    return any(bool(os.environ.get(name)) for name in names)


def file_present(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def command_version(command: str) -> str | None:
    try:
        completed = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0].strip() if output else None


def build_report(strict: bool = False) -> dict[str, Any]:
    mcp = mcp_snapshot()
    missing_install: list[str] = []
    missing_auth: list[str] = []
    warnings: list[str] = []
    next_steps: list[str] = []

    mcp_status: dict[str, Any] = {}
    for name in MCP_REQUIRED:
        present = mcp_present(mcp, name)
        note = mcp_auth_note(mcp, name) if present else None
        mcp_status[name] = {"present": present, "auth_note": note}
        if not present:
            missing_install.append("mcp:%s" % name)
            next_steps.extend(INSTALL_COMMANDS.get(name, []))
        elif note:
            missing_auth.append("mcp:%s" % name)
            next_steps.append(note)

    skill_status: dict[str, Any] = {}
    for name in SKILL_REQUIRED:
        path = find_skill(name)
        skill_status[name] = {"present": bool(path), "path": path}
        if not path:
            missing_install.append("skill:%s" % name)
            if name.startswith("tokenomist-"):
                key = "tokenomist"
            elif name.startswith("gate-"):
                key = "gate"
            else:
                key = name
            next_steps.extend(INSTALL_COMMANDS.get(key, []))

    cli_status = {
        "okx": bool(shutil.which("okx")),
        "tok": bool(shutil.which("tok")),
        "binance-cli": bool(shutil.which("binance-cli")),
        "deno": bool(shutil.which("deno")),
    }
    binance_version = command_version("binance-cli") if cli_status["binance-cli"] else None
    if not cli_status["okx"]:
        warnings.append("缺少 `okx` CLI；OKX 官方 market skill 不可用（MCP 仍可只读查询）。")
    if not cli_status["tok"]:
        warnings.append("缺少 `tok` CLI；Tokenomist skills 不可用。")
    if not cli_status["binance-cli"]:
        warnings.append("缺少 `binance-cli`；Binance MCP 仍可用于行情，官方 CLI skill 的完整命令不可用。")
    elif binance_version:
        try:
            major = int(binance_version.split()[-1].split(".")[0])
        except (ValueError, IndexError):
            major = 0
        if major < 2:
            warnings.append("`binance-cli` 版本低于 2.0.0；请升级到官方 release，npm 的 1.3.0 不兼容官方 skill。")
    if not cli_status["deno"]:
        warnings.append("缺少 Deno；CoinGecko MCP 的 Code Mode 可能不可用。")

    credentials = {
        "coinGecko": env_present("COINGECKO_DEMO_API_KEY", "COINGECKO_PRO_API_KEY"),
        "coinMarketCap": env_present("CMC_MCP_API_KEY", "COINMARKETCAP_API_KEY"),
        "tokenomist": env_present("TOKENOMIST_API_KEY") or file_present(Path.home() / ".tokenomist" / "config.json"),
        "bybit": env_present("BYBIT_API_KEY"),
        "okx": env_present("OKX_API_KEY") or file_present(Path.home() / ".okx" / "config.toml"),
        "binance": env_present("BINANCE_API_KEY") or env_present("BINANCE_SECRET_KEY"),
        "glassnode": env_present("GLASSNODE_API_KEY"),
        "etherscan": env_present("ETHERSCAN_API_KEY"),
    }

    optional_sources = {
        "cryptoPanic": env_present("CRYPTOPANIC_API_KEY"),
        "fred": env_present("FRED_API_KEY"),
        "tradingEconomics": env_present("TRADING_ECONOMICS_API_KEY"),
        "bls": env_present("BLS_API_KEY"),
        "x": env_present("X_BEARER_TOKEN"),
        "reddit": env_present("REDDIT_CLIENT_ID"),
    }

    if not credentials["coinGecko"]:
        warnings.append("未检测到 CoinGecko key；可 keyless 受限运行，但必须降低数据质量评级。")
    if not credentials["coinMarketCap"]:
        missing_auth.append("credential:CMC_MCP_API_KEY")
        next_steps.append("申请 CMC key: https://pro.coinmarketcap.com/login ，然后 export CMC_MCP_API_KEY=...")
    if not credentials["tokenomist"]:
        missing_auth.append("credential:TOKENOMIST_API_KEY")
        next_steps.append("申请 Tokenomist key: https://tokenomist.ai ，然后运行 `tok auth login` 或 export TOKENOMIST_API_KEY=...")
    if not credentials["bybit"]:
        warnings.append("未检测到 Bybit key；公共行情可用，账户数据不可用。")
    if not credentials["okx"]:
        warnings.append("未检测到 OKX OAuth/API key；公共行情可用，账户与情绪数据不可用。")
    if not credentials["binance"]:
        warnings.append("未检测到 Binance API key；MCP 需要完成 OAuth，CLI 账户数据不可用。")
    if not credentials["glassnode"]:
        warnings.append("Glassnode MCP 以公共模式运行；只能读取最近 30 天数据，设置 `GLASSNODE_API_KEY` 可解除时间范围限制。")
    if not credentials["etherscan"]:
        missing_auth.append("credential:ETHERSCAN_API_KEY")
        next_steps.append("申请 Etherscan key: https://etherscan.io/myapikey ，然后 export ETHERSCAN_API_KEY=... 并重启 Codex。")

    if not any(optional_sources.values()):
        warnings.append("未检测到宏观/新闻/社交的可选 key；核心行情分析可运行，但宏观与情绪数据质量会降级。")

    if "mcp:binance" in missing_auth:
        next_steps.append("运行 `codex mcp login binance` 完成 OAuth。")
    if "mcp:defillama" in missing_auth:
        next_steps.append("购买/激活 DefiLlama API 计划后运行 `codex mcp login defillama`：https://defillama.com/subscribe")

    blocked = bool(missing_install) or (strict and bool(missing_auth))
    if blocked:
        status = "blocked"
    elif missing_auth:
        status = "ready_with_warnings"
    else:
        status = "ready"

    report = {
        "status": status,
        "strict": strict,
        "missing_install": sorted(set(missing_install)),
        "missing_auth": sorted(set(missing_auth)),
        "warnings": sorted(set(warnings)),
        "mcp": mcp_status,
        "skills": skill_status,
        "cli": cli_status,
        "cli_versions": {"binance-cli": binance_version},
        "credentials_present": credentials,
        "optional_sources_present": optional_sources,
        "next_steps": list(dict.fromkeys(next_steps)),
        "note": "只检查名称/路径/环境变量是否存在，不读取或打印密钥。",
    }
    return report


def print_human(report: dict[str, Any]) -> None:
    print("status:", report["status"])
    for key in ("missing_install", "missing_auth", "warnings"):
        values = report.get(key) or []
        print("%s:" % key)
        if not values:
            print("  - none")
        for value in values:
            print("  -", value)
    print("cli:", json.dumps(report["cli"], ensure_ascii=False))
    if report.get("next_steps"):
        print("next_steps:")
        for step in report["next_steps"]:
            print("  -", step)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check external dependencies for the trading skill")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--strict", action="store_true", help="treat missing credentials/OAuth as blocking")
    args = parser.parse_args()

    report = build_report(strict=args.strict)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)

    if report["status"] == "blocked":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

