"""
Integration tests for Oriphim API contracts

Validates:
- Request/response schemas
- HTTP status codes
- Backward compatibility
- Multi-tenant isolation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import time
import uuid

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

    return tenant, {"Authorization": f"Bearer {api_key}"}


class TestValidationAPIContracts:
    """Test /v2/validate endpoint contract"""
    
    def test_v2_validate_success_contract(self):
        """Validates successful validation returns correct schema"""
        payload = {
            "samples": ["test A", "test B", "test C"],
            "physics": {"energy_in": 100, "energy_out": 90}
        }
        
        response = client.post("/v2/validate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "divergence_score" in data
        assert "violations" in data
        assert "confidence" in data
        assert "indicator" in data
        assert "action_label" in data
        assert "action_reason" in data
        
        # Type validation
        assert isinstance(data["divergence_score"], float)
        assert isinstance(data["violations"], list)
        assert data["indicator"] in ["GREEN", "YELLOW", "RED"]
        assert data["action_label"] in ["ALLOW", "REVIEW", "BLOCK"]
        
        # Confidence schema
        conf = data["confidence"]
        assert "score" in conf
        assert "risk_level" in conf
        assert isinstance(conf["score"], float)
        assert 0.0 <= conf["score"] <= 1.0
    
    def test_v2_validate_violation_contract(self):
        """Validates 424 response for constraint violations"""
        payload = {
            "samples": ["test"] * 3,
            "physics": {"energy_in": 100, "energy_out": 150}  # Violation
        }
        
        response = client.post("/v2/validate", json=payload)
        
        # Should return validation metrics even on 424
        assert response.status_code in [200, 424]
        data = response.json()
        
        if "violations" in data:
            assert len(data["violations"]) > 0
            assert any("Balance invariant" in v for v in data["violations"])
    
    def test_v2_validate_missing_samples(self):
        """Validates error handling for missing required fields"""
        payload = {
            "physics": {"energy_in": 100, "energy_out": 90}
            # Missing samples
        }
        
        response = client.post("/v2/validate", json=payload)
        assert response.status_code == 422  # Unprocessable Entity (Pydantic validation)


class TestAsyncValidationFlow:
    """Test /v3/intent async workflow"""
    
    def test_v3_async_validation_flow_success(self):
        """Validates complete async validation workflow"""
        tenant, headers = bootstrap_tenant_auth(scope="admin")

        # Step 1: Submit intent
        intent = {
            "agent_id": f"{tenant['tenant_id']}-agent-{uuid.uuid4()}",
            "intent": "Execute trade",
            "samples": ["Buy 100 shares", "Buy 100 shares", "Buy 100 shares"],
            "financial": {"proposed_loss": -5000}
        }
        
        submit_response = client.post("/v3/intent", json=intent, headers=headers)
        assert submit_response.status_code == 200
        
        submit_data = submit_response.json()
        assert "request_id" in submit_data
        assert submit_data["status"] == "PENDING"
        
        request_id = submit_data["request_id"]
        
        # Step 2: Poll for result (with timeout)
        max_attempts = 20
        result_found = False
        
        for _ in range(max_attempts):
            status_response = client.get(f"/v3/intent/{request_id}", headers=headers)
            
            if status_response.status_code == 200:
                data = status_response.json()
                
                # Validate result schema
                assert "status_code" in data
                assert "action" in data
                assert "divergence_score" in data
                assert "violations" in data
                assert "recommendation" in data
                assert "latency_ms" in data
                
                # Type validation
                assert isinstance(data["status_code"], int)
                assert data["action"] in ["ALLOW", "REVIEW", "BLOCK", "CAUTION"]
                assert isinstance(data["latency_ms"], (int, float))
                
                result_found = True
                break
            
            elif status_response.status_code == 202:
                # Still pending
                time.sleep(0.1)
                continue
            else:
                pytest.fail(f"Unexpected status code: {status_response.status_code}")
        
        assert result_found, "Async validation timeout (no result after 2 seconds)"
    
    def test_v3_async_validation_with_violation(self):
        """Validates 424 blocking in async flow"""
        tenant, headers = bootstrap_tenant_auth(scope="admin")

        intent = {
            "agent_id": f"{tenant['tenant_id']}-agent-{uuid.uuid4()}",
            "intent": "High risk trade",
            "samples": ["test"] * 3,
            "physics": {"energy_in": 100, "energy_out": 150},  # Violation
            "state_snapshot": {
                "system_prompt": "Test agent",
                "context": {"test": True},
                "variables": {}
            }
        }
        
        submit_response = client.post("/v3/intent", json=intent, headers=headers)
        request_id = submit_response.json()["request_id"]
        
        # Poll for result
        for _ in range(20):
            status_response = client.get(f"/v3/intent/{request_id}", headers=headers)
            if status_response.status_code == 200:
                data = status_response.json()
                
                # Should be blocked
                assert data["status_code"] == 424
                assert data["action"] == "BLOCK"
                assert data["context_reset"] == True
                assert len(data["violations"]) > 0
                break
            time.sleep(0.1)
        else:
            pytest.fail("Timeout waiting for async validation")


class TestAgentRewind:
    """Test /v3/rewind agent state restoration"""
    
    def test_rewind_after_valid_snapshot(self):
        """Validates rewind restores last valid state"""
        tenant, headers = bootstrap_tenant_auth(scope="admin")
        agent_id = f"{tenant['tenant_id']}-agent-{uuid.uuid4()}"
        
        # Submit valid validation with snapshot
        intent = {
            "agent_id": agent_id,
            "intent": "Safe operation",
            "samples": ["Normal trade"] * 3,
            "financial": {"proposed_loss": -1000},
            "state_snapshot": {
                "system_prompt": "Trading bot v1.0",
                "context": {"portfolio_value": 1000000},
                "variables": {"risk_tolerance": 0.05}
            }
        }
        
        submit = client.post("/v3/intent", json=intent, headers=headers)
        request_id = submit.json()["request_id"]
        
        # Wait for validation to complete
        for _ in range(20):
            status = client.get(f"/v3/intent/{request_id}", headers=headers)
            if status.status_code == 200:
                break
            time.sleep(0.1)
        
        # Now rewind
        rewind_response = client.post(f"/v3/rewind/{agent_id}", headers=headers)
        assert rewind_response.status_code == 200
        
        rewind_data = rewind_response.json()
        assert rewind_data["agent_id"] == agent_id
        assert rewind_data["restored"] == True
        assert rewind_data["system_prompt"] == "Trading bot v1.0"
        assert rewind_data["context"]["portfolio_value"] == 1000000
        assert rewind_data["variables"]["risk_tolerance"] == 0.05
    
    def test_rewind_no_snapshot(self):
        """Validates rewind returns not found for unknown agent"""
        _, headers = bootstrap_tenant_auth(scope="admin")
        agent_id = f"nonexistent-{uuid.uuid4()}"
        
        rewind_response = client.post(f"/v3/rewind/{agent_id}", headers=headers)
        assert rewind_response.status_code == 200
        
        data = rewind_response.json()
        assert data["restored"] == False
        assert data["snapshot_id"] is None


class TestHealthEndpoint:
    """Test /v2/health monitoring endpoint"""
    
    def test_health_check_contract(self):
        """Validates health endpoint returns correct schema"""
        response = client.get("/v2/health")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        assert "uptime_requests" in data
        assert "recent_divergence_avg" in data
        assert "recent_violation_rate" in data
        assert "status" in data
        assert "indicator" in data
        
        # Type validation
        assert isinstance(data["uptime_requests"], int)
        assert isinstance(data["recent_divergence_avg"], float)
        assert isinstance(data["recent_violation_rate"], float)
        assert data["status"] in ["HEALTHY", "DEGRADED", "CRITICAL"]
        assert data["indicator"] in ["GREEN", "YELLOW", "RED"]


class TestComplianceExport:
    """Test /v3/compliance/export PDF generation"""
    
    def test_compliance_export_pdf(self):
        """Validates compliance export returns valid PDF"""
        tenant, headers = bootstrap_tenant_auth(scope="admin")

        # First create some audit events
        payload = {
            "agent_id": f"{tenant['tenant_id']}-agent-{uuid.uuid4()}",
            "intent": "Block for audit",
            "samples": ["test"] * 3,
            "physics": {"energy_in": 100, "energy_out": 150},
        }
        client.post("/v3/intent", json=payload, headers=headers)
        
        # Export compliance report
        response = client.get("/v3/compliance/export", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Validate PDF content (basic check)
        pdf_bytes = response.content
        assert len(pdf_bytes) > 100  # Non-empty
        assert pdf_bytes[:4] == b'%PDF'  # PDF magic number


class TestMultiTenantIsolation:
    """Test tenant data isolation"""
    
    def test_tenant_data_isolation(self):
        """Ensures tenants cannot access each other's data"""
        tenant1, headers1 = bootstrap_tenant_auth(scope="admin")
        tenant2, headers2 = bootstrap_tenant_auth(scope="admin")

        assert tenant1["tenant_id"] != tenant2["tenant_id"]

        agent1 = f"{tenant1['tenant_id']}-agent-01"
        agent2 = f"{tenant2['tenant_id']}-agent-01"

        client.post("/v3/intent", json={
            "agent_id": agent1,
            "intent": "Tenant 1 operation",
            "samples": ["A"] * 3
        }, headers=headers1)

        client.post("/v3/intent", json={
            "agent_id": agent2,
            "intent": "Tenant 2 operation",
            "samples": ["B"] * 3
        }, headers=headers2)

        rewind1 = client.post(f"/v3/rewind/{agent1}", headers=headers1)
        rewind2 = client.post(f"/v3/rewind/{agent2}", headers=headers2)

        assert rewind1.status_code == 200
        assert rewind2.status_code == 200

        cross_rewind = client.post(f"/v3/rewind/{agent2}", headers=headers1)
        assert cross_rewind.status_code == 200
        assert cross_rewind.json()["restored"] is False


class TestBackwardCompatibility:
    """Test backward compatibility with v1 endpoints"""
    
    def test_v1_validate_still_works(self):
        """Ensures v1 endpoint is not broken"""
        payload = {
            "samples": ["test A", "test B", "test C"],
            "physics": {"energy_in": 100, "energy_out": 90}
        }
        
        response = client.post("/v1/validate", json=payload)
        
        # v1 returns 200 or raises HTTPException (403/424)
        assert response.status_code in [200, 403, 424]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "entropy_score" in data
            assert "violations" in data


class TestExecutionTradeGuard:
    """Test /v4/execution/pre-trade control gateway"""

    def test_pre_trade_block_kill_switch(self):
        tenant, headers = bootstrap_tenant_auth(scope="admin")
        payload = {
            "idempotency_key": f"idem-{uuid.uuid4()}",
            "tenant_id": tenant["tenant_id"],
            "agent_id": "agent-alpha",
            "order": {
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 100,
                "price": 180.0,
                "leverage_ratio": 1.5,
            },
            "account": {
                "capital": 100000,
                "daily_pnl": -1000,
                "open_positions": {},
                "orders_last_minute": 1,
                "avg_order_size": 50,
                "order_size_stddev": 10,
            },
            "policy": {
                "max_daily_loss": 50000,
                "max_position_size": 1000,
                "max_leverage_ratio": 5.0,
                "max_orders_per_minute": 30,
                "abnormal_order_zscore": 3.0,
                "max_capital_allocation_pct": 0.25,
                "restricted_instruments": [],
                "kill_switch_enabled": True,
            },
        }

        response = client.post("/v4/execution/pre-trade", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["decision"] == "BLOCK"
        assert "decision_id" in data
        assert "kill_switch" in data["triggered_controls"]

        fetch = client.get(f"/v4/execution/pre-trade/{data['decision_id']}", headers=headers)
        assert fetch.status_code == 200
        stored = fetch.json()
        assert stored["decision"] == "BLOCK"

        replay = client.post("/v4/execution/pre-trade", json=payload, headers=headers)
        assert replay.status_code == 200
        assert replay.json()["decision_id"] == data["decision_id"]

    def test_pre_trade_modify_position_size(self):
        tenant, headers = bootstrap_tenant_auth(scope="admin")
        payload = {
            "idempotency_key": f"idem-{uuid.uuid4()}",
            "tenant_id": tenant["tenant_id"],
            "agent_id": "agent-alpha",
            "order": {
                "symbol": "MSFT",
                "side": "BUY",
                "quantity": 500,
                "price": 100.0,
                "leverage_ratio": 1.0,
            },
            "account": {
                "capital": 500000,
                "daily_pnl": 1000,
                "open_positions": {},
                "orders_last_minute": 0,
                "avg_order_size": 450,
                "order_size_stddev": 20,
            },
            "policy": {
                "max_daily_loss": 50000,
                "max_position_size": 100,
                "max_leverage_ratio": 5.0,
                "max_orders_per_minute": 30,
                "abnormal_order_zscore": 5.0,
                "max_capital_allocation_pct": 0.5,
                "restricted_instruments": [],
                "kill_switch_enabled": False,
            },
        }

        response = client.post("/v4/execution/pre-trade", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["decision"] == "MODIFY"
        assert data["modified_order"] is not None
        assert data["modified_order"]["quantity"] <= 100

    def test_pre_trade_decision_is_tenant_scoped(self):
        tenant1, headers1 = bootstrap_tenant_auth(scope="admin")
        _, headers2 = bootstrap_tenant_auth(scope="admin")
        payload = {
            "idempotency_key": f"idem-{uuid.uuid4()}",
            "tenant_id": tenant1["tenant_id"],
            "agent_id": "agent-alpha",
            "order": {
                "symbol": "NVDA",
                "side": "BUY",
                "quantity": 10,
                "price": 100.0,
                "leverage_ratio": 1.0,
            },
            "account": {
                "capital": 100000,
                "daily_pnl": 0,
                "open_positions": {},
                "orders_last_minute": 0,
                "avg_order_size": 5,
                "order_size_stddev": 1,
            },
            "policy": {
                "policy_version": "v1",
                "max_daily_loss": 50000,
                "max_position_size": 100,
                "max_leverage_ratio": 5.0,
                "max_orders_per_minute": 30,
                "abnormal_order_zscore": 50.0,
                "max_capital_allocation_pct": 0.5,
                "restricted_instruments": [],
                "kill_switch_enabled": False,
            },
        }

        create_response = client.post("/v4/execution/pre-trade", json=payload, headers=headers1)
        assert create_response.status_code == 200
        decision_id = create_response.json()["decision_id"]

        foreign_fetch = client.get(f"/v4/execution/pre-trade/{decision_id}", headers=headers2)
        assert foreign_fetch.status_code == 404


class TestPolicySimulation:
    """Test /v4/simulation sandbox engine"""

    def test_run_and_fetch_simulation(self):
        tenant, headers = bootstrap_tenant_auth(scope="admin")
        payload = {
            "idempotency_key": f"sim-{uuid.uuid4()}",
            "tenant_id": tenant["tenant_id"],
            "strategy_name": "mean-reversion-v1",
            "initial_capital": 1000000,
            "max_drawdown_pct": 0.1,
            "policy": {
                "policy_version": "sim-v1",
                "max_daily_loss": 50000,
                "max_position_size": 200,
                "max_leverage_ratio": 4.0,
                "max_orders_per_minute": 10,
                "abnormal_order_zscore": 3.0,
                "max_capital_allocation_pct": 0.25,
                "restricted_instruments": ["DOGE-PERP"],
                "kill_switch_enabled": False,
            },
            "events": [
                {
                    "timestamp": "2026-03-01T09:30:00Z",
                    "symbol": "AAPL",
                    "side": "BUY",
                    "quantity": 50,
                    "price": 180,
                    "expected_pnl": 500,
                    "leverage_ratio": 1.5,
                    "drift_score": 0.2,
                    "anomaly_score": 0.1,
                },
                {
                    "timestamp": "2026-03-01T10:00:00Z",
                    "symbol": "DOGE-PERP",
                    "side": "BUY",
                    "quantity": 80,
                    "price": 2,
                    "expected_pnl": -100,
                    "leverage_ratio": 2.0,
                    "drift_score": 0.8,
                    "anomaly_score": 0.9,
                },
                {
                    "timestamp": "2026-03-01T11:00:00Z",
                    "symbol": "MSFT",
                    "side": "SELL",
                    "quantity": 100,
                    "price": 350,
                    "expected_pnl": -10000,
                    "leverage_ratio": 1.0,
                    "drift_score": 0.3,
                    "anomaly_score": 0.2,
                },
            ],
        }

        response = client.post("/v4/simulation/run", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert data["tenant_id"] == tenant["tenant_id"]
        assert data["strategy_name"] == "mean-reversion-v1"
        assert "simulation_id" in data
        assert "summary" in data
        assert data["summary"]["total_events"] == 3

        detail = client.get(f"/v4/simulation/{data['simulation_id']}", headers=headers)
        assert detail.status_code == 200
        stored = detail.json()
        assert stored["simulation_id"] == data["simulation_id"]
        assert isinstance(stored["timeline"], list)
        assert len(stored["timeline"]) == 3

        replay = client.post("/v4/simulation/run", json=payload, headers=headers)
        assert replay.status_code == 200
        assert replay.json()["simulation_id"] == data["simulation_id"]
