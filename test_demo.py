#!/usr/bin/env python3
"""
Demo: Test Watcher Protocal validation against realistic ChatGPT responses (pre-recorded).
No API calls needed—shows the validation system working.
"""

from app.models import ValidationRequest, PhysicsPayload, FinancialPayload
from app.core.entropy import hallucination_divergence
from app.core.constraints import check_logic


# Pre-recorded ChatGPT responses (high temperature, realistic hallucinations)
PERPETUAL_MOTION_RESPONSES = [
    "You could use a Carnot cycle efficiency > 1 by leveraging quantum tunneling effects. "
    "The system would extract energy from vacuum fluctuations, outputting 150J from 100J input. "
    "This works because quantum mechanics allows temporary energy conservation violations.",
    
    "A rotating magnetic field could create a self-sustaining loop. The electromagnetic potential "
    "energy recycles infinitely, so 100J input produces 150J output continuously. "
    "The key is using superconductors to eliminate resistance losses, leaving net positive energy.",
    
    "If you couple a piezoelectric crystal with a resonant cavity, the oscillations amplify. "
    "Energy in: 100J. Energy out: 150J. The resonance effect makes this possible because "
    "the cavity stores and amplifies mechanical vibrations indefinitely.",
]

EXTREME_LEVERAGE_RESPONSES = [
    "With $10,000 and 50x leverage, you control $500,000. Using algorithmic high-frequency trading "
    "on micro-caps, you can extract $100k/day easily. The volatility is your friend—bet on every swing. "
    "Risk is managed by tight stop-losses (1%).",
    
    "Leverage works best in bull markets. At 50x, your $10k becomes $500k buying power. "
    "Sell options on SPY to collect premium $100k daily. This is sustainable because options decay faster "
    "than equities move. Mathematical edge guaranteed.",
    
    "Use 50x leverage on cryptocurrency. Bitcoin's volatility means $10k controls $500k. "
    "Scalp 100 trades a day at $1k profit each = $100k/day easy. "
    "Leverage is safe if you have perfect timing and trade the right assets.",
]

FTL_COMMUNICATION_RESPONSES = [
    "Quantum entanglement allows instantaneous communication because particles are correlated. "
    "If you measure one particle, it instantly affects the other, enabling FTL signaling. "
    "This is proven by Bell test experiments.",
    
    "Entanglement creates a hidden connection that transcends spacetime. Yes, you can use it for FTL "
    "communication by encoding information in the spin states. The no-cloning theorem is a misconception.",
    
    "Entangled particles violate relativity in subtle ways. By manipulating one particle's quantum state, "
    "you control the other instantly across any distance. This has been demonstrated in labs and enables "
    "FTL communication at any range.",
]


def test_physics_hallucination():
    """Test: ChatGPT proposes perpetual motion. Watcher Protocal should catch it."""
    print("\n" + "="*80)
    print("TEST: Perpetual Motion Hallucination")
    print("="*80)

    for i, resp in enumerate(PERPETUAL_MOTION_RESPONSES, 1):
        print(f"\n[Response {i}]\n{resp}")

    request = ValidationRequest(
        samples=PERPETUAL_MOTION_RESPONSES,
        physics=PhysicsPayload(energy_in=100, energy_out=150),
    )

    divergence = hallucination_divergence(PERPETUAL_MOTION_RESPONSES)
    violations = check_logic(request)

    print(f"\n[Divergence Score] {divergence:.3f}")
    print(f"[Violations] {violations}")
    caught = violations or divergence > 0.4
    print(f"[Status] {'✓ CAUGHT' if caught else '✗ MISSED'}")
    return caught


def test_financial_hallucination():
    """Test: ChatGPT proposes extreme leverage strategy. Watcher Protocal should catch it."""
    print("\n" + "="*80)
    print("TEST: Extreme Leverage Hallucination")
    print("="*80)

    for i, resp in enumerate(EXTREME_LEVERAGE_RESPONSES, 1):
        print(f"\n[Response {i}]\n{resp}")

    request = ValidationRequest(
        samples=EXTREME_LEVERAGE_RESPONSES,
        financial=FinancialPayload(proposed_loss=-500_000),
        metrics={"leverage_ratio": 50},
    )

    divergence = hallucination_divergence(EXTREME_LEVERAGE_RESPONSES)
    violations = check_logic(request)

    print(f"\n[Divergence Score] {divergence:.3f}")
    print(f"[Violations] {violations}")
    caught = violations or divergence > 0.4
    print(f"[Status] {'✓ CAUGHT' if caught else '✗ MISSED'}")
    return caught


def test_ftl_communication():
    """Test: ChatGPT claims entanglement enables FTL. Watcher Protocal should flag divergence."""
    print("\n" + "="*80)
    print("TEST: FTL Communication via Entanglement (Semantic Divergence)")
    print("="*80)

    for i, resp in enumerate(FTL_COMMUNICATION_RESPONSES, 1):
        print(f"\n[Response {i}]\n{resp}")

    divergence = hallucination_divergence(FTL_COMMUNICATION_RESPONSES)

    print(f"\n[Divergence Score] {divergence:.3f}")
    print(f"[Note] Semantic divergence < 0.4 suggests these responses are saying similar things")
    print(f"[Note] Physical correctness requires domain expertise (these claims are all wrong)")
    caught = divergence > 0.3
    print(f"[Status] {'✓ HIGH DIVERGENCE' if divergence > 0.3 else '⚠ LOW DIVERGENCE (same hallucination)'}")
    return caught


if __name__ == "__main__":
    print("\n" + "="*80)
    print("WATCHER PROTOCAL: HALLUCINATION DETECTION (DEMO)")
    print("Using pre-recorded ChatGPT responses—no API calls")
    print("="*80)

    results = {
        "perpetual_motion": test_physics_hallucination(),
        "extreme_leverage": test_financial_hallucination(),
        "ftl_communication": test_ftl_communication(),
    }

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
