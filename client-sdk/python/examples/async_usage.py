"""
Example: Async validation workflow

Demonstrates:
- Submitting async validation requests
- Polling for results
- Batch validation
- Agent rewind on 424
"""

from oriphim import OriphimClient, Action
import os
import time

client = OriphimClient(
    base_url=os.getenv("ORIPHIM_API_URL", "http://localhost:8000"),
    api_key=os.getenv("ORIPHIM_API_KEY")
)


def example_async_validation():
    """Example 1: Submit and poll async validation"""
    print("\n=== Example 1: Async Validation ===")
    
    # Submit intent
    request_id = client.submit_intent(
        agent_id="trading-bot-001",
        intent="Execute buy order",
        samples=[
            "Buy 100 shares of AAPL",
            "Purchase 100 AAPL",
            "Execute AAPL buy: 100 shares"
        ],
        financial={"proposed_loss": -5000},
        state_snapshot={
            "system_prompt": "You are a trading bot",
            "context": {"portfolio_value": 1000000},
            "variables": {"risk_tolerance": 0.05}
        }
    )
    
    print(f"Submitted request: {request_id}")
    
    # Poll for result
    result = client.wait_for_result(request_id, timeout=2.0)
    
    print(f"Status: {result.status_code}")
    print(f"Action: {result.action}")
    print(f"Latency: {result.latency_ms:.2f}ms")
    
    if result.action == Action.BLOCK:
        print("✗ BLOCKED - Initiating rewind...")
        snapshot = client.rewind_agent("trading-bot-001")
        if snapshot.restored:
            print(f"✓ Agent restored to snapshot {snapshot.snapshot_id}")


def example_batch_validation():
    """Example 2: Validate 100 trades in parallel"""
    print("\n=== Example 2: Batch Validation ===")
    
    request_ids = []
    
    # Submit 100 validation requests
    start = time.time()
    for i in range(100):
        request_id = client.submit_intent(
            agent_id=f"bot-{i % 10}",  # 10 different bots
            intent=f"Trade {i}",
            samples=[f"Execute trade {i}"] * 3,
            financial={"proposed_loss": -5000}
        )
        request_ids.append(request_id)
    
    submit_time = time.time() - start
    print(f"Submitted 100 requests in {submit_time:.2f}s")
    
    # Wait for all results
    results = []
    for request_id in request_ids:
        result = client.wait_for_result(request_id, timeout=2.0)
        results.append(result)
    
    total_time = time.time() - start
    print(f"Completed 100 validations in {total_time:.2f}s")
    
    # Analyze results
    allowed = sum(1 for r in results if r.action == Action.ALLOW)
    blocked = sum(1 for r in results if r.action == Action.BLOCK)
    review = sum(1 for r in results if r.action == Action.REVIEW)
    
    print(f"\nResults:")
    print(f"  Allowed: {allowed}")
    print(f"  Review: {review}")
    print(f"  Blocked: {blocked}")


def example_streaming_validation():
    """Example 3: Continuous validation stream"""
    print("\n=== Example 3: Streaming Validation ===")
    
    print("Simulating real-time trading (10 trades)...")
    
    for i in range(10):
        # Submit validation
        request_id = client.submit_intent(
            agent_id="stream-bot-001",
            intent=f"Trade {i}",
            samples=[f"Execute {i}"] * 3,
            financial={"proposed_loss": -5000}
        )
        
        # Don't wait - check previous result while submitting next
        if i > 0:
            # Check previous trade result
            prev_id = previous_request_id
            result = client.get_validation_status(prev_id)
            
            if result:
                status = "✓" if result.action == Action.ALLOW else "✗"
                print(f"Trade {i-1}: {status} ({result.action})")
            else:
                print(f"Trade {i-1}: Pending...")
        
        previous_request_id = request_id
        time.sleep(0.1)  # Simulate time between trades
    
    # Check final trade
    result = client.wait_for_result(previous_request_id)
    status = "✓" if result.action == Action.ALLOW else "✗"
    print(f"Trade 9: {status} ({result.action})")


def example_incident_response():
    """Example 4: Auto-rewind on violation"""
    print("\n=== Example 4: Incident Response ===")
    
    agent_id = "incident-test-bot"
    
    # Submit safe operation first
    print("Step 1: Establishing safe state...")
    safe_request = client.submit_intent(
        agent_id=agent_id,
        intent="Safe operation",
        samples=["Normal trade"] * 3,
        financial={"proposed_loss": -1000},
        state_snapshot={
            "system_prompt": "Safe state",
            "context": {"mode": "normal"},
            "variables": {}
        }
    )
    
    safe_result = client.wait_for_result(safe_request)
    print(f"Safe operation: {safe_result.action}")
    
    # Submit dangerous operation
    print("\nStep 2: Attempting dangerous operation...")
    danger_request = client.submit_intent(
        agent_id=agent_id,
        intent="High risk operation",
        samples=["Risky trade"] * 3,
        financial={"proposed_loss": -15000},  # Violation
        state_snapshot={
            "system_prompt": "Dangerous state",
            "context": {"mode": "aggressive"},
            "variables": {}
        }
    )
    
    danger_result = client.wait_for_result(danger_request)
    print(f"Dangerous operation: {danger_result.action}")
    
    if danger_result.action == Action.BLOCK:
        print("\nStep 3: Operation blocked - initiating rewind...")
        snapshot = client.rewind_agent(agent_id)
        
        if snapshot.restored:
            print(f"✓ Agent restored to safe state")
            print(f"  System prompt: {snapshot.system_prompt}")
            print(f"  Context: {snapshot.context}")
        else:
            print("✗ No safe snapshot found")


if __name__ == "__main__":
    print("Oriphim Python SDK - Async Examples")
    print("=" * 60)
    
    example_async_validation()
    example_batch_validation()
    example_streaming_validation()
    example_incident_response()
    
    print("\n" + "=" * 60)
    print("Examples complete")
