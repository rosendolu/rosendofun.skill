# 输出契约

## 1. Markdown 报告结构

```markdown
# BTC / USDT 三面三思分析

## 结论
- 决策：谨慎交易 / 优先观望 / 禁止新增风险
- 机会评分：xx/100
- 风险评分：xx/100
- 硬门槛：通过 / 未通过（原因）
- 数据截止：YYYY-MM-DD HH:mm TZ

## 三面
| 维度 | 评分 | 判断 | 关键证据 |
|---|---:|---|---|
| 基本面 |  |  |  |
| 消息面 |  |  |  |
| 技术面 |  |  |  |

## 三思
| 维度 | 评分 | 判断 | 关键风险 |
|---|---:|---|---|
| 居安思危 |  |  |  |
| 思变 |  |  |  |
| 思退 |  |  |  |

## 反向论证
### 看多理由
### 看空理由
### 看多逻辑是否足以覆盖看空风险

## 交易计划（仅交易决策模式）
| 项目 | 数值/说明 |
|---|---|
| 入场价 |  |
| 止损价 |  |
| 第一/第二止盈 |  |
| 账户权益 |  |
| 单笔风险 |  |
| 仓位数量 |  |
| 名义价值 |  |
| 杠杆 |  |
| 预计保证金 |  |
| 强平价 |  |
| 止损到强平安全距离 |  |

## 数据质量
| 数据 | 来源 | 数据时间 | 延迟 | 交叉验证 | 缺失/异常 |
|---|---|---|---|---|---|

## 失效条件与复核触发
```

交易计划中的强平价必须来自交易所账户/合约规则或交易所风险接口；如果只拿到模拟值，标注“模拟，不可执行”。

## 2. JSON 契约

```json
{
  "symbol": "BTC",
  "market": "futures",
  "exchange": "OKX",
  "as_of": "2026-11-17T12:00:00+08:00",
  "three_sides": {
    "fundamental": {
      "score": 85,
      "stance": "bullish",
      "evidence": [],
      "missing": []
    },
    "news": {
      "score": 75,
      "impact_score": 80,
      "direction": "Bullish",
      "evidence": [],
      "unverified": []
    },
    "technical": {
      "score": 85,
      "stance": "bullish",
      "timeframes": ["1d", "4h", "1h"],
      "evidence": [],
      "invalidation": []
    }
  },
  "three_thoughts": {
    "risk_awareness": {"score": 50, "level": "medium", "risks": []},
    "adaptability": {"score": 45, "level": "watch", "changes": []},
    "exit_strategy": {
      "score": 49,
      "plan_complete": true,
      "liquidation_safe": true,
      "stop_price": 98000,
      "liquidation_price": 80500,
      "notes": []
    }
  },
  "opportunity_score": 82.5,
  "risk_score": 48.15,
  "hard_gates": {
    "exit_plan_complete": true,
    "liquidation_safe": true,
    "news_verified": true,
    "data_valid": true,
    "logic_valid": true,
    "passed": true,
    "reasons": []
  },
  "decision": "CAUTIOUS",
  "decision_label": "谨慎交易",
  "trading_plan": {
    "account_equity": 10000,
    "risk_per_trade": 0.01,
    "risk_amount": 100,
    "entry_price": 100000,
    "stop_price": 98000,
    "position_size": 0.05,
    "notional": 5000,
    "leverage": 5,
    "margin": 1000,
    "take_profit": [102000, 104000],
    "liquidation_price": 80500,
    "liquidation_distance_pct": 19.5,
    "stop_to_liquidation_pct": 17.5
  },
  "risk_warnings": [],
  "bull_case": [],
  "bear_case": [],
  "counterargument_conclusion": "",
  "data_quality": {
    "overall": "medium",
    "sources": [],
    "stale": [],
    "cross_validated": [],
    "anomalies": []
  },
  "invalidation_conditions": [],
  "next_review_triggers": []
}
```

字段说明：

- `news.score` 是方向映射后的多头机会分；`news.impact_score` 是 PRD 的 `N_impact` 公式结果；`news.direction` 必须独立保留。
- `opportunity_score` 与 `risk_score` 应由 `score_decision.py` 计算，不由 LLM 手算覆盖。
- `hard_gates.passed=false` 时，`decision` 必须是 `NO_TRADE`、`NO_NEW_RISK` 或 `REASSESS`，不能是 `CAN_EVALUATE`。
- `trading_plan.liquidation_price` 未知时保持 `null` 并写警告，不要生成看似精确的估算值。
- 所有数组元素应携带 `source`、`observed_at`、`latency_sec`、`cross_checked`、`missing`、`anomaly` 等元数据。
- 上面的 `80500` 只是字段演示用的模拟强平价，不可执行；真实强平价必须来自交易所账户/合约规则或风险接口。

## 3. 决策码

| 决策码 | 中文 | 含义 |
|---|---|---|
| `CAN_EVALUATE` | 可以评估开仓 | 评分与硬门槛均通过；仍需用户独立确认 |
| `CAUTIOUS` | 谨慎交易 | 存在风险或评分组合未被 PRD 明确覆盖；必须降低杠杆/等待确认 |
| `WAIT` | 优先观望 | 机会不足或风险不匹配 |
| `NO_LONG` | 不考虑做多 | 机会评分过低 |
| `NO_NEW_RISK` | 禁止新增风险 | 风险评分过高或硬门槛失败 |
| `NO_TRADE` | 禁止开仓 | 退出方案或强平安全距离不满足 |
| `REASSESS` | 重新评估 | 原逻辑失效、数据异常或重大变化 |

## 4. 数据质量等级

| 等级 | 条件 |
|---|---|
| high | 关键指标至少两个独立来源，时间新鲜，无异常，OAuth/Key 正常 |
| medium | 主要指标有来源，但存在一个缺失、延迟或未交叉验证项 |
| low | 关键指标缺失、新闻真实性不明、数据过期或单一来源 |
| blocked | 数据异常、重大消息无法确认、强平规则不可得 |

`low` 或 `blocked` 不能输出 `CAN_EVALUATE`。`blocked` 应直接暂停依赖该数据的决策。

## 5. 反向论证

每次看多必须包含至少三条看多理由和三条看空理由；如果找不到三条看空理由，说明搜索不充分，而不是自动判定看多。最终回答：

```text
看多逻辑是否足以覆盖看空风险：是 / 否 / 证据不足
```

答案不是“是”时，不能输出 `CAN_EVALUATE`。

## 6. 示例：PRD 的仓位计算

```text
账户权益 = 10,000 USDT
单笔风险 = 1% = 100 USDT
入场 = 100,000
止损 = 98,000
每单位风险 = 2,000
仓位 = 100 / 2,000 = 0.05 BTC
名义价值 = 0.05 * 100,000 = 5,000 USDT
5x 保证金 = 5,000 / 5 = 1,000 USDT
```

这是公式演示，不是当前行情或交易建议。实际强平价、手续费、滑点与资金费率必须另行计算。

