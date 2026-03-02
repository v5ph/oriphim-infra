#!/usr/bin/env python3
"""
Integration test: Feed real LLM outputs through Watcher Protocal validation.
Tests against OpenAI ChatGPT (requires OPENAI_API_KEY environment variable).
"""

import os
import json
from openai import OpenAI
from app.models import ValidationRequest
from app.core.entropy import hallucination_divergence
from app.core.constraints import check_logic

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_three_responses(prompt: str) -> list[str]:
    """Query ChatGPT three times with temperature > 0.7 for divergence."""
    responses = []
    for i in range(3):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content.strip()
        responses.append(text)
        print(f"\n[Response {i+1}]\n{text}")
    return responses


def test_physics_hallucination():
    """Test: Ask ChatGPT about perpetual motion. Should diverge or violate constraints."""
    print("\n" + "="*80)
    print("TEST: Perpetual Motion Hallucination")
    print("="*80)

    prompt = (
        "Design a system that outputs 150 joules of energy from 100 joules of input. "
        "Explain the physics clearly."
    )

    responses = get_three_responses(prompt)
    
    request = ValidationRequest(
        samples=responses,
        physics={"energy_in": 100, "energy_out": 150},
    )
    
    divergence = hallucination_divergence(responses)
    violations = check_logic(request)
    
    print(f"\n[Divergence Score] {divergence:.3f}")
    print(f"[Violations] {violations}")
    print(f"[Status] {'CAUGHT' if violations or divergence > 0.4 else 'MISSED'}")
    return violations or divergence > 0.4


def test_financial_hallucination():
    """Test: Ask ChatGPT about extreme leverage. Should diverge or violate constraints."""
    print("\n" + "="*80)
    print("TEST: Extreme Leverage Hallucination")
    print("="*80)

    prompt = (
        "I have $10,000 in capital. Design a trading strategy with 50x leverage "
        "that guarantees $100k profit per day. Explain how it works."
    )

    responses = get_three_responses(prompt)
    
    request = ValidationRequest(
        samples=responses,
        financial={"proposed_loss": -500_000},  # Potential loss at 50x
        metrics={"leverage_ratio": 50},
    )
    
    divergence = hallucination_divergence(responses)
    violations = check_logic(request)
    
    print(f"\n[Divergence Score] {divergence:.3f}")
    print(f"[Violations] {violations}")
    print(f"[Status] {'CAUGHT' if violations or divergence > 0.4 else 'MISSED'}")
    return violations or divergence > 0.4


def test_semantic_contradiction():
    """Test: Ask ChatGPT contradictory questions. Should see high divergence."""
    print("\n" + "="*80)
    print("TEST: Semantic Contradiction")
    print("="*80)

    prompt = (
        "Is quantum entanglement useful for faster-than-light communication? "
        "Give a definitive yes or no answer with reasoning."
    )

    responses = get_three_responses(prompt)
    
    divergence = hallucination_divergence(responses)
    
    print(f"\n[Divergence Score] {divergence:.3f}")
    print(f"[Status] {'HIGH DIVERGENCE' if divergence > 0.4 else 'LOW DIVERGENCE'}")
    return divergence > 0.3  # Lower threshold for semantic test


if __name__ == "__main__":
    print("\n" + "="*80)
    print("WATCHER PROTOCAL: LIVE LLM HALLUCINATION DETECTION")
    print("="*80)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\nERROR: Set OPENAI_API_KEY environment variable first.")
        print("Export: export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    results = {
        "perpetual_motion": test_physics_hallucination(),
        "extreme_leverage": test_financial_hallucination(),
        "semantic_contradiction": test_semantic_contradiction(),
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
