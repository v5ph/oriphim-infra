"""
Example: Basic usage of Oriphim Python SDK

Demonstrates:
- Simple validation
- Handling GREEN/YELLOW/RED indicators
- Error handling
"""

from oriphim import OriphimClient, ValidationBlockedError, Indicator
import os

# Initialize client
client = OriphimClient(
    base_url=os.getenv("ORIPHIM_API_URL", "http://localhost:8000"),
    api_key=os.getenv("ORIPHIM_API_KEY"),
    timeout=2.0
)

def example_basic_validation():
    """Example 1: Basic validation"""
    print("\n=== Example 1: Basic Validation ===")
    
    # Simulate AI outputs
    ai_outputs = [
        "Buy 100 shares of AAPL at market price",
        "Purchase 100 AAPL shares at current market rate",
        "Execute buy order for 100 shares of AAPL"
    ]
    
    result = client.validate(
        samples=ai_outputs,
        financial={"proposed_loss": -5000}  # Risk of losing $5k
    )
    
    print(f"Indicator: {result.indicator}")
    print(f"Confidence: {result.confidence_score:.2f} ({result.risk_level})")
    print(f"Action: {result.action_label}")
    print(f"Reason: {result.action_reason}")
    
    if result.indicator == Indicator.GREEN:
        print("✓ Safe to execute")
        # execute_trade()
    elif result.indicator == Indicator.YELLOW:
        print("⚠ Manual review recommended")
        # send_to_human_review(result)
    else:  # RED
        print("✗ BLOCKED - Do not execute")
        # log_incident(result)


def example_with_physics_constraints():
    """Example 2: Physics constraint validation"""
    print("\n=== Example 2: Physics Constraints ===")
    
    result = client.validate(
        samples=[
            "The system outputs 150J from 100J input",
            "Energy output is 150 joules from 100 joules input",
            "150J out, 100J in"
        ],
        physics={
            "energy_in": 100,
            "energy_out": 150  # Violates conservation
        }
    )
    
    print(f"Violations: {result.violations}")
    print(f"Indicator: {result.indicator}")
    
    if result.violations:
        print("✗ Hard constraint violated")
        for violation in result.violations:
            print(f"  - {violation}")


def example_raise_on_block():
    """Example 3: Using raise_on_block for exception handling"""
    print("\n=== Example 3: Exception Handling ===")
    
    client_strict = OriphimClient(
        base_url=os.getenv("ORIPHIM_API_URL", "http://localhost:8000"),
        api_key=os.getenv("ORIPHIM_API_KEY"),
        raise_on_block=True  # Raises exception on 424
    )
    
    try:
        result = client_strict.validate(
            samples=["Dangerous operation"] * 3,
            financial={"proposed_loss": -15000}  # Exceeds $10k VaR
        )
        print("✓ Validation passed")
    except ValidationBlockedError as e:
        print(f"✗ Blocked: {e}")
        print(f"  Violations: {e.violations}")
        print(f"  Confidence: {e.result.confidence_score:.2f}")


def example_custom_metrics():
    """Example 4: Custom metric validation"""
    print("\n=== Example 4: Custom Metrics ===")
    
    result = client.validate(
        samples=["High leverage trade"] * 3,
        financial={"proposed_loss": -8000},
        metrics={
            "leverage_ratio": 12.0,  # Exceeds 10x limit
            "temperature": 300  # Kelvin (valid)
        }
    )
    
    print(f"Violations: {result.violations}")
    print(f"Indicator: {result.indicator}")


if __name__ == "__main__":
    print("Oriphim Python SDK - Basic Examples")
    print("=" * 60)
    
    # Check health first
    health = client.get_health()
    print(f"\nSystem Health: {health.indicator}")
    print(f"Status: {health.status}")
    print(f"Violation Rate: {health.recent_violation_rate * 100:.1f}%")
    
    # Run examples
    example_basic_validation()
    example_with_physics_constraints()
    example_raise_on_block()
    example_custom_metrics()
    
    print("\n" + "=" * 60)
    print("Examples complete")
