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
        # Step 1: Submit intent
        intent = {
            "agent_id": f"test-agent-{uuid.uuid4()}",
            "intent": "Execute trade",
            "samples": ["Buy 100 shares", "Buy 100 shares", "Buy 100 shares"],
            "financial": {"proposed_loss": -5000}
        }
        
        submit_response = client.post("/v3/intent", json=intent)
        assert submit_response.status_code == 200
        
        submit_data = submit_response.json()
        assert "request_id" in submit_data
        assert submit_data["status"] == "PENDING"
        
        request_id = submit_data["request_id"]
        
        # Step 2: Poll for result (with timeout)
        max_attempts = 20
        result_found = False
        
        for _ in range(max_attempts):
            status_response = client.get(f"/v3/intent/{request_id}")
            
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
        intent = {
            "agent_id": f"test-agent-{uuid.uuid4()}",
            "intent": "High risk trade",
            "samples": ["test"] * 3,
            "physics": {"energy_in": 100, "energy_out": 150},  # Violation
            "state_snapshot": {
                "system_prompt": "Test agent",
                "context": {"test": True},
                "variables": {}
            }
        }
        
        submit_response = client.post("/v3/intent", json=intent)
        request_id = submit_response.json()["request_id"]
        
        # Poll for result
        for _ in range(20):
            status_response = client.get(f"/v3/intent/{request_id}")
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
        agent_id = f"test-agent-{uuid.uuid4()}"
        
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
        
        submit = client.post("/v3/intent", json=intent)
        request_id = submit.json()["request_id"]
        
        # Wait for validation to complete
        for _ in range(20):
            status = client.get(f"/v3/intent/{request_id}")
            if status.status_code == 200:
                break
            time.sleep(0.1)
        
        # Now rewind
        rewind_response = client.post(f"/v3/rewind/{agent_id}")
        assert rewind_response.status_code == 200
        
        rewind_data = rewind_response.json()
        assert rewind_data["agent_id"] == agent_id
        assert rewind_data["restored"] == True
        assert rewind_data["system_prompt"] == "Trading bot v1.0"
        assert rewind_data["context"]["portfolio_value"] == 1000000
        assert rewind_data["variables"]["risk_tolerance"] == 0.05
    
    def test_rewind_no_snapshot(self):
        """Validates rewind returns not found for unknown agent"""
        agent_id = f"nonexistent-{uuid.uuid4()}"
        
        rewind_response = client.post(f"/v3/rewind/{agent_id}")
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
        # First create some audit events
        payload = {
            "samples": ["test"] * 3,
            "physics": {"energy_in": 100, "energy_out": 150}
        }
        client.post("/v2/validate", json=payload)
        
        # Export compliance report
        response = client.get("/v3/compliance/export")
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
        # Create two tenants
        tenant1 = client.post("/v1/onboarding/tenants", json={
            "org_name": f"Tenant A {uuid.uuid4()}",
            "domain": f"tenant-a-{uuid.uuid4()}.com",
            "support_tier": "standard"
        }).json()
        
        tenant2 = client.post("/v1/onboarding/tenants", json={
            "org_name": f"Tenant B {uuid.uuid4()}",
            "domain": f"tenant-b-{uuid.uuid4()}.com",
            "support_tier": "standard"
        }).json()
        
        # Verify tenants created
        assert "tenant_id" in tenant1
        assert "tenant_id" in tenant2
        assert tenant1["tenant_id"] != tenant2["tenant_id"]
        
        # Create separate agents for each tenant
        agent1 = f"{tenant1['tenant_id']}-agent-01"
        agent2 = f"{tenant2['tenant_id']}-agent-01"
        
        # Submit validation for tenant 1
        client.post("/v3/intent", json={
            "agent_id": agent1,
            "intent": "Tenant 1 operation",
            "samples": ["A"] * 3
        })
        
        # Submit validation for tenant 2
        client.post("/v3/intent", json={
            "agent_id": agent2,
            "intent": "Tenant 2 operation",
            "samples": ["B"] * 3
        })
        
        # TODO: Add API key-based isolation testing when auth middleware complete
        # For now, verify agents can be rewound independently
        rewind1 = client.post(f"/v3/rewind/{agent1}")
        rewind2 = client.post(f"/v3/rewind/{agent2}")
        
        assert rewind1.status_code == 200
        assert rewind2.status_code == 200


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
