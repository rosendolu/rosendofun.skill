#!/usr/bin/env python3
"""Deterministic scoring, decision gating and position sizing."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


DECISION_LABELS = {
    "CAN_EVALUATE": "可以评估开仓",
    "CAUTIOUS": "谨慎交易",
    "WAIT": "优先观望",
    "NO_LONG": "不考虑做多",
    "NO_NEW_RISK": "禁止新增风险",
    "NO_TRADE": "禁止开仓",
    "REASSESS": "重新评估",
}


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def numeric(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        raise ValueError("missing numeric field: %s" % key)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("field %s must be numeric" % key) from exc


def optional_numeric(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    return numeric(payload, key)


def score_0_100(payload: dict[str, Any], key: str) -> float:
    value = numeric(payload, key)
    if not 0 <= value <= 100:
        raise ValueError("%s must be between 0 and 100" % key)
    return value


def directional_news_score(impact: float, direction: str) -> float:
    normalized = direction.strip().lower()
    if normalized == "bullish":
        return clamp(50 + 0.50 * impact)
    if normalized == "bearish":
        return clamp(50 - 0.50 * impact)
    if normalized == "neutral":
        return 50.0
    if normalized == "uncertain":
        return clamp(50 - 0.25 * impact)
    raise ValueError("news_direction must be Bullish, Bearish, Neutral or Uncertain")


def base_decision(opportunity: float, risk: float) -> str:
    # PRD table plus conservative handling for combinations it does not cover.
    if risk >= 70:
        return "NO_NEW_RISK"
    if opportunity >= 80:
        return "CAN_EVALUATE" if risk <= 30 else "CAUTIOUS"
    if opportunity >= 60:
        return "CAUTIOUS" if risk <= 40 else "WAIT"
    if opportunity >= 40:
        return "WAIT"
    return "NO_LONG"


def downgrade(decision: str) -> str:
    if decision == "CAN_EVALUATE":
        return "CAUTIOUS"
    if decision == "CAUTIOUS":
        return "WAIT"
    return decision


def calculate_plan(payload: dict[str, Any], warnings: list[str]) -> dict[str, Any] | None:
    if not all(payload.get(key) is not None for key in ("account_equity", "risk_per_trade", "entry_price", "stop_price")):
        return None

    equity = numeric(payload, "account_equity")
    risk_per_trade = numeric(payload, "risk_per_trade")
    entry = numeric(payload, "entry_price")
    stop = numeric(payload, "stop_price")
    leverage_value = optional_numeric(payload, "leverage")
    leverage = 1.0 if leverage_value is None else leverage_value
    liquidation = optional_numeric(payload, "liquidation_price")

    if equity <= 0 or entry <= 0 or stop <= 0 or leverage <= 0:
        raise ValueError("account_equity, entry_price, stop_price and leverage must be positive")
    if not 0 < risk_per_trade <= 1:
        raise ValueError("risk_per_trade must be a decimal in (0, 1], e.g. 0.01 for 1%")
    if entry == stop:
        raise ValueError("entry_price must differ from stop_price")

    risk_amount = equity * risk_per_trade
    per_unit_risk = abs(entry - stop)
    position_size = risk_amount / per_unit_risk
    notional = position_size * entry
    margin = notional / leverage
    side = str(payload.get("side", "long")).lower()
    if side not in {"long", "short"}:
        raise ValueError("side must be long or short")

    plan: dict[str, Any] = {
        "side": side,
        "account_equity": equity,
        "risk_per_trade": risk_per_trade,
        "risk_amount": risk_amount,
        "entry_price": entry,
        "stop_price": stop,
        "position_size": position_size,
        "notional": notional,
        "leverage": leverage,
        "margin": margin,
        "take_profit": payload.get("take_profit", []),
        "liquidation_price": liquidation,
        "liquidation_distance_pct": None,
        "stop_distance_pct": abs(entry - stop) / entry * 100,
        "stop_to_liquidation_pct": None,
        "liquidation_verified": liquidation is not None,
    }

    if liquidation is not None:
        plan["liquidation_distance_pct"] = abs(entry - liquidation) / entry * 100
        plan["stop_to_liquidation_pct"] = abs(stop - liquidation) / entry * 100
        if side == "long" and stop <= liquidation:
            plan["liquidation_verified"] = False
            warnings.append("止损价未早于强平价（long），强平安全门槛不通过。")
        if side == "short" and stop >= liquidation:
            plan["liquidation_verified"] = False
            warnings.append("止损价未早于强平价（short），强平安全门槛不通过。")
    else:
        warnings.append("未提供强平价；不得把此计划视为可执行，必须用交易所账户与合约规则复核。")

    return plan


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    fundamental = score_0_100(payload, "fundamental")
    technical = score_0_100(payload, "technical")
    risk_awareness = score_0_100(payload, "risk_awareness")
    adaptability = score_0_100(payload, "adaptability")
    exit_strategy = score_0_100(payload, "exit_strategy")

    if payload.get("news") is not None:
        news = score_0_100(payload, "news")
        news_source = "provided_directional_score"
    elif payload.get("news_impact") is not None and payload.get("news_direction") is not None:
        news_impact = score_0_100(payload, "news_impact")
        news = directional_news_score(news_impact, str(payload["news_direction"]))
        news_source = "mapped_from_impact_and_direction"
    else:
        raise ValueError("provide news, or both news_impact and news_direction")

    opportunity = 0.30 * fundamental + 0.25 * news + 0.45 * technical
    risk = 0.35 * risk_awareness + 0.30 * adaptability + 0.35 * exit_strategy

    hard = {
        "exit_plan_complete": bool(payload.get("exit_plan_complete", False)),
        "liquidation_safe": bool(payload.get("liquidation_safe", False)),
        "news_verified": bool(payload.get("news_verified", True)),
        "data_valid": bool(payload.get("data_valid", True)),
        "logic_valid": bool(payload.get("logic_valid", True)),
    }
    reasons: list[str] = []

    plan = calculate_plan(payload, warnings)
    if plan and plan.get("liquidation_verified") is False:
        hard["liquidation_safe"] = False

    if not hard["exit_plan_complete"]:
        reasons.append("思退方案缺失：禁止开仓。")
    if not hard["liquidation_safe"]:
        reasons.append("强平安全距离不足或未验证：禁止开仓。")
    if not hard["data_valid"]:
        reasons.append("交易所/行情数据异常：暂停依赖该数据的决策。")
    if not hard["logic_valid"]:
        reasons.append("原有交易逻辑失效：触发重新评估。")

    decision = base_decision(opportunity, risk)
    if not hard["exit_plan_complete"] or not hard["liquidation_safe"] or not hard["data_valid"]:
        decision = "NO_TRADE"
    elif not hard["logic_valid"]:
        decision = "REASSESS"
    elif not hard["news_verified"]:
        decision = downgrade(decision)
        warnings.append("重大消息真实性无法确认：降低交易权限。")

    if decision == "NO_NEW_RISK":
        warnings.append("风险评分 >= 70：风险优先，禁止新增风险。")

    hard["passed"] = not reasons
    hard["reasons"] = reasons

    return {
        "scores": {
            "fundamental": fundamental,
            "news": news,
            "news_source": news_source,
            "technical": technical,
            "risk_awareness": risk_awareness,
            "adaptability": adaptability,
            "exit_strategy": exit_strategy,
        },
        "formulas": {
            "opportunity": "0.30F + 0.25N + 0.45T",
            "risk": "0.35W + 0.30V + 0.35E",
            "position_size": "equity * risk_per_trade / abs(entry - stop)",
            "margin": "position_size * entry / leverage",
        },
        "opportunity_score": round(opportunity, 2),
        "risk_score": round(risk, 2),
        "base_decision": base_decision(opportunity, risk),
        "decision": decision,
        "decision_label": DECISION_LABELS[decision],
        "hard_gates": hard,
        "trading_plan": plan,
        "warnings": warnings,
    }


def load_payload(path: str | None) -> dict[str, Any]:
    if path and path != "-":
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a Three Sides / Three Thoughts trade setup")
    parser.add_argument("--input-json", help="JSON file; omit or use - to read stdin")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    try:
        payload = load_payload(args.input_json)
        result = evaluate(payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2) if args.json else "error: %s" % exc)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("opportunity:", result["opportunity_score"])
        print("risk:", result["risk_score"])
        print("decision:", result["decision"], result["decision_label"])
        print("hard_gates:", json.dumps(result["hard_gates"], ensure_ascii=False))
        for warning in result["warnings"]:
            print("-", warning)
    return 0


if __name__ == "__main__":
    sys.exit(main())

