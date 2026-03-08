"""
Performance tests using Locust for load testing

Install: pip install locust

Run: locust -f tests/performance/locustfile.py --host http://localhost:8000
"""

from locust import HttpUser, task, between, events
import random
import json
import uuid


class OriphimUser(HttpUser):
    """Simulates a high-frequency trading client using Oriphim"""
    
    wait_time = between(0.05, 0.2)  # 50-200ms between requests (realistic for HFT)
    
    def on_start(self):
        """Setup: Initialize agent ID for this user"""
        self.agent_id = f"loadtest-agent-{uuid.uuid4()}"
    
    @task(weight=60)
    def validate_normal_trade(self):
        """Normal validation (60% of traffic) - should pass"""
        payload = {
            "samples": [
                f"Execute trade {random.randint(1, 10000)}",
                f"Buy {random.randint(1, 1000)} shares",
                f"Trade ID: {uuid.uuid4()}"
            ],
            "financial": {
                "proposed_loss": random.uniform(-9000, -1000)  # Within $10k limit
            },
            "metrics": {
                "leverage_ratio": random.uniform(1.0, 9.5)  # Within 10x limit
            }
        }
        
        with self.client.post(
            "/v2/validate",
            json=payload,
            catch_response=True,
            name="/v2/validate [normal]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("indicator") == "GREEN":
                    response.success()
                else:
                    response.failure(f"Unexpected indicator: {data.get('indicator')}")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(weight=15)
    def validate_violation(self):
        """Submit trades that violate constraints (15% of traffic) - should block"""
        violation_type = random.choice(["financial", "physics", "leverage"])
        
        if violation_type == "financial":
            payload = {
                "samples": ["High risk trade"] * 3,
                "financial": {"proposed_loss": -15000}  # Exceeds $10k VaR
            }
        elif violation_type == "physics":
            payload = {
                "samples": ["Impossible system"] * 3,
                "physics": {
                    "energy_in": 100,
                    "energy_out": 150  # Violates conservation
                }
            }
        else:  # leverage
            payload = {
                "samples": ["Extreme leverage"] * 3,
                "metrics": {"leverage_ratio": 25.0}  # Exceeds 10x limit
            }
        
        with self.client.post(
            "/v2/validate",
            json=payload,
            catch_response=True,
            name="/v2/validate [violation]"
        ) as response:
            # Expect blocking or warning
            if response.status_code in [200, 400, 424]:
                data = response.json()
                if len(data.get("violations", [])) > 0 or data.get("indicator") == "RED":
                    response.success()
                else:
                    response.failure("Violation not detected")
            else:
                response.failure(f"Unexpected status {response.status_code}")
    
    @task(weight=15)
    def async_validation_flow(self):
        """Async validation workflow (15% of traffic)"""
        # Submit intent
        intent = {
            "agent_id": self.agent_id,
            "intent": f"Trade {random.randint(1, 1000)}",
            "samples": [f"Execute order {uuid.uuid4()}"] * 3,
            "financial": {"proposed_loss": random.uniform(-9000, -1000)},
            "state_snapshot": {
                "system_prompt": "Trading bot",
                "context": {"portfolio": 1000000},
                "variables": {}
            }
        }
        
        with self.client.post(
            "/v3/intent",
            json=intent,
            catch_response=True,
            name="/v3/intent [submit]"
        ) as response:
            if response.status_code == 200:
                request_id = response.json().get("request_id")
                response.success()
                
                # Poll for result (simulate async workflow)
                self.poll_validation_result(request_id)
            else:
                response.failure(f"Status {response.status_code}")
    
    def poll_validation_result(self, request_id: str, max_attempts: int = 10):
        """Poll for async validation result"""
        for attempt in range(max_attempts):
            with self.client.get(
                f"/v3/intent/{request_id}",
                catch_response=True,
                name="/v3/intent/:id [poll]"
            ) as response:
                if response.status_code == 200:
                    # Validation complete
                    response.success()
                    return
                elif response.status_code == 202:
                    # Still pending
                    if attempt == max_attempts - 1:
                        response.failure("Timeout waiting for validation")
                    else:
                        response.success()  # Expected
                else:
                    response.failure(f"Unexpected status {response.status_code}")
                    return
    
    @task(weight=10)
    def check_health(self):
        """CRO polling health endpoint (10% of traffic)"""
        with self.client.get(
            "/v2/health",
            catch_response=True,
            name="/v2/health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "indicator" in data and data["indicator"] in ["GREEN", "YELLOW", "RED"]:
                    response.success()
                else:
                    response.failure("Invalid health response schema")
            else:
                response.failure(f"Status {response.status_code}")


class CRODashboardUser(HttpUser):
    """Simulates a CRO dashboard polling for metrics"""
    
    wait_time = between(2, 5)  # Poll every 2-5 seconds
    
    @task
    def poll_health(self):
        """Poll health endpoint"""
        self.client.get("/v2/health")


# Locust event hooks for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*60)
    print("ORIPHIM LOAD TEST STARTED")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*60)
    print("LOAD TEST COMPLETE")
    print("="*60)
    
    stats = environment.stats
    
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"\nResponse times:")
    print(f"  P50: {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"  P95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  P99: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"  Max: {stats.total.max_response_time:.0f}ms")
    print(f"\nRequests/sec: {stats.total.total_rps:.2f}")
    
    print("\n" + "="*60)
    
    # Success criteria validation
    p95 = stats.total.get_response_time_percentile(0.95)
    failure_rate = stats.total.fail_ratio
    
    print("\nSUCCESS CRITERIA:")
    print(f" P95 latency: {p95:.0f}ms {'✓ PASS' if p95 < 100 else '✗ FAIL'} (target: <100ms)")
    print(f" Error rate: {failure_rate*100:.2f}% {'✓ PASS' if failure_rate < 0.001 else '✗ FAIL'} (target: <0.1%)")
    print(f" Throughput: {stats.total.total_rps:.2f} req/s {'✓ PASS' if stats.total.total_rps > 100 else '✗ FAIL'} (target: >100)")
    print("="*60 + "\n")
