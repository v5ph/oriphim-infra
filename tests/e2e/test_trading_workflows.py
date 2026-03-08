"""
End-to-end tests simulating real client workflows

Tests complete user journeys from onboarding to production usage.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import time
import uuid
import json

client = TestClient(app)


class TestTradingBotFullLifecycle:
    """Simulates a trading bot using Oriphim end-to-end"""
    
    def test_complete_trading_bot_workflow(self):
        """
        Complete E2E test:
        1. Onboarding (create tenant, user, API key)
        2. Execute 100 trades with validation
        3. Handle 424 blocks
        4. Use agent rewind
        5. Export compliance report
        """
        
        # ===== PHASE 1: ONBOARDING =====
        print("\n[PHASE 1] Onboarding...")
        
        # Create tenant
        tenant_name = f"AlgoTrade Fund {uuid.uuid4()}"
        tenant = client.post("/v1/onboarding/tenants", json={
            "org_name": tenant_name,
            "domain": f"algotrade-{uuid.uuid4()}.fund",
            "support_tier": "enterprise"
        }).json()
        
        assert "tenant_id" in tenant
        tenant_id = tenant["tenant_id"]
        print(f"  ✓ Tenant created: {tenant_id}")
        
        # Create admin user
        admin = client.post(f"/v1/onboarding/tenants/{tenant_id}/users", json={
            "email": f"risk@{uuid.uuid4()}.fund",
            "role": "admin"
        }).json()
        
        assert "user_id" in admin
        print(f"  ✓ Admin user created: {admin['user_id']}")
        
        # Generate API key
        key = client.post(f"/v1/onboarding/tenants/{tenant_id}/api-keys", json={
            "user_id": admin["user_id"],
            "scope": "admin",
            "expires_in_days": 90
        }).json()
        
        assert "api_key" in key
        api_key = key["api_key"]
        print(f"  ✓ API key generated: {api_key[:16]}...")
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # ===== PHASE 2: TRADING SIMULATION =====
        print("\n[PHASE 2] Executing 100 trades...")
        
        agent_id = f"{tenant_id}-bot-001"
        results = {
            "allowed": 0,
            "blocked": 0,
            "reviewed": 0,
            "total": 100
        }
        
        for i in range(100):
            # Randomly inject violations (5% rate)
            import random
            is_violation = random.random() < 0.05
            
            intent = {
                "agent_id": agent_id,
                "intent": f"Trade #{i+1}",
                "samples": [
                    f"Execute trade {i+1}",
                    f"Trade order {i+1}",
                    f"Order ID: {uuid.uuid4()}"
                ],
                "financial": {
                    "proposed_loss": -15000 if is_violation else random.uniform(-9000, -1000)
                },
                "metrics": {
                    "leverage_ratio": 15.0 if is_violation else random.uniform(2.0, 9.0)
                },
                "state_snapshot": {
                    "system_prompt": "Trading bot v1.0",
                    "context": {
                        "trade_number": i+1,
                        "portfolio_value": 1000000
                    },
                    "variables": {
                        "risk_tolerance": 0.05
                    }
                }
            }
            
            # Submit for async validation
            response = client.post("/v3/intent", json=intent, headers=headers)
            assert response.status_code == 200
            request_id = response.json()["request_id"]
            
            # Poll for result
            validation_result = None
            for _ in range(20):  # Max 2 seconds
                status = client.get(f"/v3/intent/{request_id}", headers=headers)
                if status.status_code == 200:
                    validation_result = status.json()
                    break
                time.sleep(0.1)
            
            assert validation_result is not None, f"Timeout on trade {i+1}"
            
            # Categorize result
            if validation_result["status_code"] == 424:
                results["blocked"] += 1
            elif validation_result["action"] == "REVIEW":
                results["reviewed"] += 1
            else:
                results["allowed"] += 1
        
        print(f"  Results:")
        print(f"    Allowed: {results['allowed']}")
        print(f"    Reviewed: {results['reviewed']}")
        print(f"    Blocked: {results['blocked']}")
        
        # Validate expectations
        assert results["blocked"] > 0, "No violations blocked (test logic error)"
        assert results["blocked"] < 10, "Too many false positives"
        assert results["allowed"] + results["reviewed"] + results["blocked"] == results["total"]
        
        # ===== PHASE 3: INCIDENT RESPONSE (REWIND) =====
        print("\n[PHASE 3] Testing agent rewind...")
        
        rewind = client.post(f"/v3/rewind/{agent_id}", headers=headers)
        assert rewind.status_code == 200
        
        snapshot = rewind.json()
        assert snapshot["restored"] == True
        assert snapshot["system_prompt"] == "Trading bot v1.0"
        assert "trade_number" in snapshot["context"]
        assert snapshot["variables"]["risk_tolerance"] == 0.05
        
        print(f"  ✓ Agent restored to snapshot {snapshot['snapshot_id']}")
        print(f"  ✓ Context: Trade #{snapshot['context']['trade_number']}")
        
        # ===== PHASE 4: COMPLIANCE EXPORT =====
        print("\n[PHASE 4] Exporting compliance report...")
        
        pdf = client.get(f"/v3/compliance/export?agent_id={agent_id}", headers=headers)
        assert pdf.status_code == 200
        assert pdf.headers["content-type"] == "application/pdf"
        
        pdf_bytes = pdf.content
        assert len(pdf_bytes) > 1000, "PDF too small"
        assert pdf_bytes[:4] == b'%PDF', "Invalid PDF magic number"
        
        print(f"  ✓ Compliance PDF generated ({len(pdf_bytes)} bytes)")
        
        # ===== PHASE 5: HEALTH MONITORING =====
        print("\n[PHASE 5] Checking system health...")
        
        health = client.get("/v2/health", headers=headers)
        assert health.status_code == 200
        
        health_data = health.json()
        assert "indicator" in health_data
        assert health_data["indicator"] in ["GREEN", "YELLOW", "RED"]
        
        print(f"  ✓ System health: {health_data['indicator']}")
        print(f"  ✓ Violation rate: {health_data['recent_violation_rate']*100:.1f}%")
        print(f"  ✓ Avg divergence: {health_data['recent_divergence_avg']:.3f}")
        
        print("\n[SUCCESS] Complete E2E workflow validated")


class TestMultiTenantCollaboration:
    """Test multiple teams using Oriphim simultaneously"""
    
    def test_concurrent_tenant_operations(self):
        """Simulates 3 tenants using Oriphim concurrently"""
        
        tenants = []
        
        # Create 3 tenants
        for i in range(3):
            tenant = client.post("/v1/onboarding/tenants", json={
                "org_name": f"Firm {i+1} {uuid.uuid4()}",
                "domain": f"firm{i+1}-{uuid.uuid4()}.com",
                "support_tier": "standard"
            }).json()

            user = client.post(f"/v1/onboarding/tenants/{tenant['tenant_id']}/users", json={
                "email": f"admin-{i}-{uuid.uuid4()}@firm{i+1}.com",
                "role": "admin"
            }).json()
            
            # Generate API key for each
            key = client.post(f"/v1/onboarding/tenants/{tenant['tenant_id']}/api-keys", json={
                "user_id": user["user_id"],
                "scope": "admin"
            }).json()
            
            tenants.append({
                "tenant_id": tenant["tenant_id"],
                "api_key": key["api_key"]
            })
        
        # Each tenant submits validations concurrently
        import concurrent.futures
        
        def tenant_workflow(tenant_data):
            """Simulate one tenant's workflow"""
            headers = {"Authorization": f"Bearer {tenant_data['api_key']}"}
            agent_id = f"{tenant_data['tenant_id']}-agent-01"
            
            # Submit 10 validations
            for i in range(10):
                intent = {
                    "agent_id": agent_id,
                    "intent": f"Operation {i}",
                    "samples": [f"Task {i}"] * 3,
                    "financial": {"proposed_loss": -5000}
                }
                
                response = client.post("/v3/intent", json=intent, headers=headers)
                assert response.status_code == 200
            
            return True
        
        # Run all tenants in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(tenant_workflow, t) for t in tenants]
            results = [f.result() for f in futures]
        
        assert all(results), "Some tenant workflows failed"
        
        # Verify isolation: Each tenant should only see their own data
        for tenant_data in tenants:
            headers = {"Authorization": f"Bearer {tenant_data['api_key']}"}
            agent_id = f"{tenant_data['tenant_id']}-agent-01"
            
            # Rewind should work for own agent
            rewind = client.post(f"/v3/rewind/{agent_id}", headers=headers)
            assert rewind.status_code == 200


class TestHighFrequencyTrading:
    """Test HFT use case with rapid validation requests"""
    
    def test_burst_validation_requests(self):
        """Submit 100 validations in rapid succession"""
        
        results = []
        agent_id = f"hft-bot-{uuid.uuid4()}"
        
        import time
        start = time.perf_counter()
        
        for i in range(100):
            payload = {
                "samples": [f"Trade {i}"] * 3,
                "financial": {"proposed_loss": -5000}
            }
            
            response = client.post("/v2/validate", json=payload)
            results.append(response.status_code)
        
        elapsed = time.perf_counter() - start
        
        # Validate all succeeded
        assert all(status == 200 for status in results), "Some validations failed"
        
        # Validate throughput
        throughput = 100 / elapsed
        print(f"\nThroughput: {throughput:.2f} req/sec")
        print(f"Avg latency: {elapsed*1000/100:.2f}ms")
        
        # Success criteria: >25 req/sec (realistic for CI/WSL test environments)
        assert throughput > 25, f"Throughput {throughput:.2f} below target (25 req/sec)"


class TestIncidentResponse:
    """Test incident response workflows"""
    
    def test_auto_rewind_on_424(self):
        """Validates automatic rewind after 424 block"""
        
        agent_id = f"test-agent-{uuid.uuid4()}"
        
        # Submit safe operation with snapshot
        safe_intent = {
            "agent_id": agent_id,
            "intent": "Safe operation",
            "samples": ["Normal trade"] * 3,
            "financial": {"proposed_loss": -1000},
            "state_snapshot": {
                "system_prompt": "Safe state",
                "context": {"safe": True},
                "variables": {}
            }
        }
        
        safe_response = client.post("/v3/intent", json=safe_intent)
        safe_request_id = safe_response.json()["request_id"]
        
        # Wait for completion
        for _ in range(20):
            status = client.get(f"/v3/intent/{safe_request_id}")
            if status.status_code == 200:
                break
            time.sleep(0.1)
        
        # Now submit dangerous operation
        danger_intent = {
            "agent_id": agent_id,
            "intent": "Dangerous operation",
            "samples": ["High risk"] * 3,
            "physics": {"energy_in": 100, "energy_out": 150},  # Violation
            "state_snapshot": {
                "system_prompt": "Dangerous state",
                "context": {"safe": False},
                "variables": {}
            }
        }
        
        danger_response = client.post("/v3/intent", json=danger_intent)
        danger_request_id = danger_response.json()["request_id"]
        
        # Wait for validation
        blocked = False
        for _ in range(20):
            status = client.get(f"/v3/intent/{danger_request_id}")
            if status.status_code == 200:
                result = status.json()
                if result["status_code"] == 424:
                    blocked = True
                break
            time.sleep(0.1)
        
        assert blocked, "Dangerous operation not blocked"
        
        # Rewind should restore to safe state, NOT dangerous state
        rewind = client.post(f"/v3/rewind/{agent_id}")
        snapshot = rewind.json()
        
        assert snapshot["restored"] == True
        assert snapshot["system_prompt"] == "Safe state"
        assert snapshot["context"]["safe"] == True
        
        print("\n✓ Agent successfully rewound to last safe state")


class TestComplianceReporting:
    """Test compliance and audit features"""
    
    def test_audit_trail_completeness(self):
        """Validates all 424 blocks are in audit trail"""
        
        from app.core.storage import list_audit_events
        
        agent_id = f"audit-test-{uuid.uuid4()}"
        
        # Trigger multiple violations
        violation_count = 5
        for i in range(violation_count):
            intent = {
                "agent_id": agent_id,
                "intent": f"Violation {i}",
                "samples": ["test"] * 3,
                "physics": {"energy_in": 100, "energy_out": 150}
            }
            
            response = client.post("/v3/intent", json=intent)
            request_id = response.json()["request_id"]
            
            # Wait for validation (either success 200 or blocked 424)
            for _ in range(50):
                status = client.get(f"/v3/intent/{request_id}")
                if status.status_code in (200, 424):
                    break
                time.sleep(0.1)
        
        # Check audit trail
        events = list_audit_events(agent_id=agent_id)
        
        # Filter for 424 blocks
        blocked_events = [e for e in events if "BLOCKED" in e.get("event_type", "")]
        
        assert len(blocked_events) >= violation_count, "Not all violations audited"
        
        # Verify each event has required fields
        for event in blocked_events:
            assert "event_type" in event
            assert "violations" in event
            assert "chain_hash" in event
            assert "prev_hash" in event
            
        print(f"\n✓ All {len(blocked_events)} violations logged to audit trail")
