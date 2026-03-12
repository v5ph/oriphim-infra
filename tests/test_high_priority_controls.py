import os
import uuid

os.environ.setdefault("DATABASE_ENCRYPTION_KEY", "0" * 64)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-" + ("x" * 48))
os.environ.setdefault("ORIPHIM_DISABLE_EMBEDDINGS", "true")

from fastapi.testclient import TestClient

from app.core.onboarding import _connect as onboarding_connect
from app.core.trade_guard import evaluate_pre_trade
from app.main import app
from app.models import AccountSnapshot, TradeOrder, TradePolicyConfig


client = TestClient(app)


def bootstrap_tenant_auth(scope: str = "admin"):
    suffix = uuid.uuid4().hex[:12]
    tenant_response = client.post(
        "/v1/onboarding/tenants",
        json={
            "org_name": f"Tenant {suffix}",
            "domain": f"tenant-{suffix}.example.com",
            "support_tier": "standard",
        },
    )
    assert tenant_response.status_code == 201
    tenant = tenant_response.json()

    user_response = client.post(
        f"/v1/onboarding/tenants/{tenant['tenant_id']}/users",
        json={"email": f"admin-{suffix}@example.com", "role": "admin", "mfa_enabled": True},
    )
    assert user_response.status_code == 201
    user = user_response.json()

    key_response = client.post(
        f"/v1/onboarding/tenants/{tenant['tenant_id']}/api-keys",
        json={"user_id": user["user_id"], "scope": scope, "expires_in_days": 30},
    )
    assert key_response.status_code == 201
    api_key = key_response.json()["api_key"]
    return tenant, user, {"Authorization": f"Bearer {api_key}"}, api_key


def test_api_key_digest_is_persisted_and_used_for_validation():
    tenant, user, _, api_key = bootstrap_tenant_auth()

    conn = onboarding_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT api_key_digest FROM api_keys WHERE tenant_id = ? AND user_id = ?",
        (tenant["tenant_id"], user["user_id"]),
    )
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row["api_key_digest"] is not None
    assert len(row["api_key_digest"]) == 64

    login_response = client.post(
        "/v1/onboarding/auth/login",
        json={"api_key": api_key, "user_agent": "pytest", "ip_address": "127.0.0.1"},
    )
    assert login_response.status_code == 200


def test_pre_trade_blocks_parallel_frequency_bypass():
    tenant, _, headers, _ = bootstrap_tenant_auth()
    agent_id = f"{tenant['tenant_id']}-agent-risk"

    request_payload = {
        "tenant_id": tenant["tenant_id"],
        "agent_id": agent_id,
        "order": {
            "symbol": "BTCUSD",
            "side": "BUY",
            "quantity": 1.0,
            "price": 100.0,
            "leverage_ratio": 1.0,
        },
        "account": {
            "capital": 100000.0,
            "daily_pnl": 0.0,
            "orders_last_minute": 0,
        },
        "policy": {
            "policy_version": "p1",
            "max_daily_loss": 10000.0,
            "max_position_size": 10.0,
            "max_leverage_ratio": 5.0,
            "max_orders_per_minute": 1,
            "abnormal_order_zscore": 10.0,
            "max_capital_allocation_pct": 1.0,
        },
    }

    first = client.post(
        "/v4/execution/pre-trade",
        headers=headers,
        json={**request_payload, "idempotency_key": "freq-allow-0001"},
    )
    second = client.post(
        "/v4/execution/pre-trade",
        headers=headers,
        json={**request_payload, "idempotency_key": "freq-block-0002"},
    )

    assert first.status_code == 200
    assert first.json()["decision"] == "ALLOW"
    assert second.status_code == 200
    assert second.json()["decision"] == "BLOCK"
    assert "trading_frequency_cap" in second.json()["triggered_controls"]


def test_pre_trade_is_idempotent_for_same_request():
    tenant, _, headers, _ = bootstrap_tenant_auth()
    payload = {
        "idempotency_key": "same-request-0001",
        "tenant_id": tenant["tenant_id"],
        "agent_id": f"{tenant['tenant_id']}-agent-idem",
        "order": {
            "symbol": "ETHUSD",
            "side": "BUY",
            "quantity": 1.0,
            "price": 100.0,
            "leverage_ratio": 1.0,
        },
        "account": {"capital": 100000.0, "daily_pnl": 0.0},
        "policy": {
            "policy_version": "p1",
            "max_daily_loss": 10000.0,
            "max_position_size": 10.0,
            "max_leverage_ratio": 5.0,
            "max_orders_per_minute": 30,
            "abnormal_order_zscore": 10.0,
            "max_capital_allocation_pct": 1.0,
        },
    }

    first = client.post("/v4/execution/pre-trade", headers=headers, json=payload)
    second = client.post("/v4/execution/pre-trade", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["decision_id"] == second.json()["decision_id"]


def test_trade_guard_uses_pending_and_unsettled_exposure():
    order = TradeOrder(symbol="BTCUSD", side="BUY", quantity=5.0, price=100.0, leverage_ratio=1.0)
    account = AccountSnapshot(
        capital=100000.0,
        daily_pnl=0.0,
        open_positions={"BTCUSD": 4.0},
        pending_orders={"BTCUSD": 3.0},
        unsettled_positions={"BTCUSD": 2.0},
    )
    policy = TradePolicyConfig(max_position_size=10.0, max_capital_allocation_pct=1.0)

    result = evaluate_pre_trade(order=order, account=account, policy=policy)

    assert result["decision"] in {"BLOCK", "MODIFY"}
    assert "max_position_size" in result["triggered_controls"]


def test_trade_guard_modified_order_respects_tick_and_lot_rules():
    order = TradeOrder(symbol="BTCUSD", side="BUY", quantity=4.37, price=101.37, leverage_ratio=1.0)
    account = AccountSnapshot(capital=1000.0, daily_pnl=0.0)
    policy = TradePolicyConfig(
        max_position_size=10.0,
        max_capital_allocation_pct=0.2,
        min_lot_size=0.25,
        tick_size=0.5,
    )

    result = evaluate_pre_trade(order=order, account=account, policy=policy)

    assert result["decision"] == "MODIFY"
    assert result["modified_order"] is not None
    assert abs((result["modified_order"]["quantity"] / 0.25) - round(result["modified_order"]["quantity"] / 0.25)) < 1e-9
    assert abs((result["modified_order"]["price"] / 0.5) - round(result["modified_order"]["price"] / 0.5)) < 1e-9


def test_privileged_actions_record_actor_identity():
    tenant, user, headers, _ = bootstrap_tenant_auth()

    analyst_response = client.post(
        f"/v1/onboarding/tenants/{tenant['tenant_id']}/users",
        headers=headers,
        json={"email": f"analyst-{uuid.uuid4().hex[:8]}@example.com", "role": "analyst", "mfa_enabled": True},
    )
    assert analyst_response.status_code == 201
    analyst_id = analyst_response.json()["user_id"]

    role_change = client.patch(
        f"/v1/onboarding/tenants/{tenant['tenant_id']}/users/{analyst_id}/role",
        headers=headers,
        json={"new_role": "viewer"},
    )
    assert role_change.status_code == 200

    audit_response = client.get(
        f"/v1/onboarding/tenants/{tenant['tenant_id']}/audit-log",
        headers=headers,
    )
    assert audit_response.status_code == 200
    events = audit_response.json()["events"]
    matching = [event for event in events if event["event_type"] == "user_role_changed" and event["target"] == analyst_id]

    assert matching
    assert matching[0]["actor_id"] == user["user_id"]