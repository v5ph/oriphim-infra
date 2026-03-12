from __future__ import annotations

from typing import Any, Dict, List

from app.models import AccountSnapshot, SimulationRequest, TradeOrder
from app.core.trade_guard import evaluate_pre_trade


def run_policy_simulation(request: SimulationRequest) -> Dict[str, Any]:
    capital = request.initial_capital
    peak_capital = request.initial_capital
    max_drawdown_observed = 0.0

    allowed_count = 0
    modified_count = 0
    review_count = 0
    blocked_count = 0
    drift_flags = 0
    anomaly_flags = 0
    policy_blocks: List[str] = []

    open_positions: Dict[str, float] = {}
    orders_last_minute = 0
    avg_order_size = 0.0

    timeline: List[Dict[str, Any]] = []

    for index, event in enumerate(request.events):
        if event.drift_score is not None and event.drift_score >= 0.7:
            drift_flags += 1
        if event.anomaly_score is not None and event.anomaly_score >= 0.7:
            anomaly_flags += 1

        stddev = max(avg_order_size * 0.4, 0.0)
        account = AccountSnapshot(
            capital=max(capital, 1.0),
            daily_pnl=capital - request.initial_capital,
            open_positions=open_positions,
            orders_last_minute=orders_last_minute,
            avg_order_size=avg_order_size,
            order_size_stddev=stddev,
        )

        order = TradeOrder(
            symbol=event.symbol,
            side=event.side,
            quantity=event.quantity,
            price=event.price,
            leverage_ratio=event.leverage_ratio,
        )

        result = evaluate_pre_trade(order=order, account=account, policy=request.policy)
        decision = result["decision"]

        if decision == "ALLOW":
            allowed_count += 1
            executed_qty = event.quantity
        elif decision == "MODIFY":
            modified_count += 1
            executed_qty = float(result["modified_order"]["quantity"])
        elif decision == "REVIEW":
            review_count += 1
            executed_qty = event.quantity
        else:
            blocked_count += 1
            executed_qty = 0.0
            policy_blocks.append(f"{event.timestamp}: {result['reason']}")

        if event.quantity > 0 and executed_qty > 0:
            scale = executed_qty / event.quantity
        else:
            scale = 0.0

        pnl_delta = event.expected_pnl * scale
        capital += pnl_delta

        if executed_qty > 0:
            direction = 1.0 if event.side == "BUY" else -1.0
            open_positions[event.symbol] = open_positions.get(event.symbol, 0.0) + (direction * executed_qty)

        orders_last_minute = min(orders_last_minute + 1, 10_000)
        avg_order_size = ((avg_order_size * index) + event.quantity) / (index + 1)

        peak_capital = max(peak_capital, capital)
        drawdown = 0.0
        if peak_capital > 0:
            drawdown = max((peak_capital - capital) / peak_capital, 0.0)
        max_drawdown_observed = max(max_drawdown_observed, drawdown)

        timeline.append(
            {
                "timestamp": event.timestamp,
                "symbol": event.symbol,
                "decision": decision,
                "capital": round(capital, 2),
                "drawdown_pct": round(drawdown, 6),
                "triggered_controls": result["triggered_controls"],
                "reason": result["reason"],
            }
        )

    summary = {
        "total_events": len(request.events),
        "allowed_count": allowed_count,
        "modified_count": modified_count,
        "review_count": review_count,
        "blocked_count": blocked_count,
        "final_capital": round(capital, 2),
        "max_drawdown_pct_observed": round(max_drawdown_observed, 6),
        "drawdown_breach": max_drawdown_observed >= request.max_drawdown_pct,
        "drift_flags": drift_flags,
        "anomaly_flags": anomaly_flags,
    }

    return {
        "summary": summary,
        "policy_blocks": policy_blocks,
        "timeline": timeline,
    }
