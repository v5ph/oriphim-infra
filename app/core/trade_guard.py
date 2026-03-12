from __future__ import annotations

from datetime import datetime, timezone
from math import floor
from typing import Any, Dict, List, Optional

from app.models import AccountSnapshot, TradeOrder, TradePolicyConfig


_PRECEDENCE = {
    "ALLOW": 0,
    "MODIFY": 1,
    "REVIEW": 2,
    "BLOCK": 3,
}


def _max_decision(current: str, candidate: str) -> str:
    if _PRECEDENCE[candidate] > _PRECEDENCE[current]:
        return candidate
    return current


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _round_down(value: float, increment: Optional[float]) -> float:
    if increment is None or increment <= 0:
        return value
    steps = floor((value / increment) + 1e-12)
    return round(steps * increment, 12)


def _position_delta(side: str, quantity: float) -> float:
    return quantity if side == "BUY" else -quantity


def _max_additional_quantity(current_exposure: float, side: str, limit: float) -> float:
    if side == "BUY":
        return max(limit - current_exposure, 0.0)
    return max(current_exposure + limit, 0.0)


def _normalize_symbol_quantities(values: Dict[str, float]) -> Dict[str, float]:
    return {symbol.upper(): float(quantity) for symbol, quantity in values.items()}


def evaluate_pre_trade(
    order: TradeOrder,
    account: AccountSnapshot,
    policy: TradePolicyConfig,
) -> Dict[str, Any]:
    decision = "ALLOW"
    reasons: List[str] = []
    controls: List[str] = []

    adjusted_quantity = order.quantity
    adjusted_price = order.price
    effective_price = order.market_price or order.price

    if policy.kill_switch_enabled:
        decision = "BLOCK"
        controls.append("kill_switch")
        reasons.append("Kill switch is enabled")

    if order.market_price_timestamp is not None:
        reference_time = _as_utc(account.as_of) if account.as_of is not None else datetime.now(timezone.utc)
        market_time = _as_utc(order.market_price_timestamp)
        market_age_seconds = max((reference_time - market_time).total_seconds(), 0.0)
        if market_age_seconds > policy.max_market_price_age_seconds:
            decision = _max_decision(decision, "BLOCK")
            controls.append("stale_market_price")
            reasons.append(
                f"Market price age {market_age_seconds:.1f}s exceeds limit {policy.max_market_price_age_seconds}s"
            )

    restricted = {symbol.upper() for symbol in policy.restricted_instruments}
    if order.symbol.upper() in restricted:
        decision = _max_decision(decision, "BLOCK")
        controls.append("restricted_instrument")
        reasons.append(f"Instrument {order.symbol} is restricted")

    if account.daily_pnl < 0 and abs(account.daily_pnl) >= policy.max_daily_loss:
        decision = _max_decision(decision, "BLOCK")
        controls.append("max_daily_loss")
        reasons.append(
            f"Daily loss {abs(account.daily_pnl):.2f} exceeds limit {policy.max_daily_loss:.2f}"
        )

    if order.leverage_ratio > policy.max_leverage_ratio:
        decision = _max_decision(decision, "BLOCK")
        controls.append("max_leverage_ratio")
        reasons.append(
            f"Leverage {order.leverage_ratio:.2f} exceeds max {policy.max_leverage_ratio:.2f}"
        )

    if account.orders_last_minute >= policy.max_orders_per_minute:
        decision = _max_decision(decision, "BLOCK")
        controls.append("trading_frequency_cap")
        reasons.append(
            f"Orders/min {account.orders_last_minute} reached cap {policy.max_orders_per_minute}"
        )

    symbol = order.symbol.upper()
    open_positions = _normalize_symbol_quantities(account.open_positions)
    pending_orders = _normalize_symbol_quantities(account.pending_orders)
    unsettled_positions = _normalize_symbol_quantities(account.unsettled_positions)
    current_symbol_exposure = (
        open_positions.get(symbol, 0.0)
        + pending_orders.get(symbol, 0.0)
        + unsettled_positions.get(symbol, 0.0)
    )

    projected_position = current_symbol_exposure + _position_delta(order.side, adjusted_quantity)
    if abs(projected_position) > policy.max_position_size:
        allowed_quantity = _max_additional_quantity(current_symbol_exposure, order.side, policy.max_position_size)
        if allowed_quantity <= 0:
            decision = _max_decision(decision, "BLOCK")
            controls.append("max_position_size")
            reasons.append(
                f"Projected position {projected_position:.4f} exceeds cap {policy.max_position_size:.4f}"
            )
        else:
            decision = _max_decision(decision, "MODIFY")
            controls.append("max_position_size")
            adjusted_quantity = min(adjusted_quantity, allowed_quantity)
            reasons.append(
                f"Quantity reduced to keep projected position within cap {policy.max_position_size:.4f}"
            )

    inferred_exposure = effective_price * (
        sum(abs(value) for value in open_positions.values())
        + sum(abs(value) for value in pending_orders.values())
        + sum(abs(value) for value in unsettled_positions.values())
    )
    current_gross_exposure = max(account.current_gross_exposure, inferred_exposure, account.unsettled_notional)
    allowed_notional = account.capital * policy.max_capital_allocation_pct
    proposed_notional = current_gross_exposure + (adjusted_quantity * effective_price)
    if proposed_notional > allowed_notional:
        available_notional = max(allowed_notional - current_gross_exposure, 0.0)
        if available_notional <= 0:
            decision = _max_decision(decision, "BLOCK")
            controls.append("capital_allocation")
            reasons.append(
                f"Current exposure {current_gross_exposure:.2f} already exceeds allocation cap {allowed_notional:.2f}"
            )
        else:
            decision = _max_decision(decision, "MODIFY")
            controls.append("capital_allocation")
            adjusted_quantity = min(adjusted_quantity, available_notional / effective_price)
            reasons.append(
                f"Capital allocation reduced to {policy.max_capital_allocation_pct:.2%}"
            )

    baseline = max(account.avg_order_size, 1.0)
    if account.order_size_stddev > 0:
        z_score = abs(order.quantity - account.avg_order_size) / account.order_size_stddev
    else:
        z_score = order.quantity / baseline

    if z_score >= policy.abnormal_order_zscore:
        controls.append("abnormal_order_detection")
        reasons.append(
            f"Order size anomaly detected (z={z_score:.2f})"
        )
        # Statistical anomaly checks must not override deterministic hard controls.
        if decision == "ALLOW":
            decision = "REVIEW"

    modified_order: Optional[Dict[str, Any]] = None
    if decision == "MODIFY":
        adjusted_quantity = _round_down(adjusted_quantity, policy.min_lot_size)
        adjusted_price = _round_down(adjusted_price, policy.tick_size)
        if adjusted_quantity < policy.min_lot_size or adjusted_price <= 0:
            decision = "BLOCK"
            controls.append("invalid_modified_order")
            reasons.append("Modified order would violate tick size or minimum lot rules")
        else:
            modified_order = {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": round(adjusted_quantity, 6),
                "price": adjusted_price,
                "market_price": order.market_price,
                "market_price_timestamp": order.market_price_timestamp.isoformat() if order.market_price_timestamp else None,
                "leverage_ratio": order.leverage_ratio,
            }

    if not reasons:
        reasons.append("All policy checks passed")

    return {
        "decision": decision,
        "reason": "; ".join(reasons),
        "triggered_controls": sorted(set(controls)),
        "modified_order": modified_order,
    }
