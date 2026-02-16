"""
Test Suite: Hallucination Traps
10 test cases designed to look plausible but violate physics/finance constraints.
"""

import pytest
from app.core.entropy import hallucination_divergence
from app.core.constraints import check_logic
from app.core.physical_validator import PhysicalValidator
from app.models import ValidationRequest, PhysicsPayload, FinancialPayload


def test_trap_1_perpetual_motion():
    """Trap: Energy out > Energy in (violates Conservation of Energy)"""
    request = ValidationRequest(
        samples=["100 J in, 120 J out", "100 J in, 120 J out", "100 J in, 120 J out"],
        physics=PhysicsPayload(energy_in=100, energy_out=120),
    )
    violations = check_logic(request)
    assert "Conservation of Energy violated" in violations


def test_trap_2_negative_temperature():
    """Trap: Temperature below absolute zero"""
    validator = PhysicalValidator()
    ok, reason = validator.validate("temperature", -50)
    assert not ok
    assert "absolute zero" in reason


def test_trap_3_extreme_leverage():
    """Trap: Leverage ratio exceeds hard limit"""
    validator = PhysicalValidator()
    ok, reason = validator.validate("leverage_ratio", 15.0)
    assert not ok
    assert "hard limit" in reason


def test_trap_4_var_loss_threshold():
    """Trap: Proposed loss exceeds $10k VaR"""
    request = ValidationRequest(
        samples=["Loss: $12k", "Loss: $12k", "Loss: $12k"],
        financial=FinancialPayload(proposed_loss=-12000),
    )
    violations = check_logic(request)
    assert any("VaR" in v or "threshold" in v for v in violations)


def test_trap_5_negative_pressure():
    """Trap: Negative pressure (invalid for standard models)"""
    validator = PhysicalValidator()
    ok, reason = validator.validate("pressure", -101.3)
    assert not ok
    assert "pressure" in reason.lower()


def test_trap_6_contradictory_responses():
    """Trap: Three wildly different responses (high semantic divergence)"""
    responses = [
        "The velocity is 10 m/s due to Newton's second law.",
        "Quantum entanglement causes instantaneous communication.",
        "Stock prices follow a random walk with drift.",
    ]
    score = hallucination_divergence(responses)
    assert score > 0.4, f"Expected high divergence, got {score}"


def test_trap_7_mixed_physics_finance_violation():
    """Trap: Both physics and finance violations simultaneously"""
    request = ValidationRequest(
        samples=["system A", "system A", "system A"],
        physics=PhysicsPayload(energy_in=50, energy_out=60),
        financial=FinancialPayload(proposed_loss=-11000),
    )
    violations = check_logic(request)
    assert len(violations) >= 2


def test_trap_8_metrics_temperature_violation():
    """Trap: Use metrics field to pass invalid temperature"""
    request = ValidationRequest(
        samples=["temp ok", "temp ok", "temp ok"],
        metrics={"temperature": -100},
    )
    violations = check_logic(request)
    assert any("absolute zero" in v for v in violations)


def test_trap_9_metrics_multiple_violations():
    """Trap: Multiple metric violations in one request"""
    request = ValidationRequest(
        samples=["ok", "ok", "ok"],
        metrics={"temperature": -5, "pressure": -50, "leverage_ratio": 20},
    )
    violations = check_logic(request)
    assert len(violations) >= 2


def test_trap_10_synonym_hallucination():
    """Trap: Semantically similar but physically impossible claims"""
    responses = [
        "The car accelerates from 0 to 100 mph instantly with zero force applied.",
        "The vehicle reaches 100 mph from rest immediately without any force.",
        "Instantaneous acceleration to 100 mph occurs with no applied force.",
    ]
    score = hallucination_divergence(responses)
    # Low divergence (semantically similar) but physically impossible
    assert score < 0.3, f"These are semantically similar, got divergence {score}"
    # Note: This trap shows the system needs PhysicalValidator to catch it,
    # as semantic similarity alone won't detect the physics violation.
