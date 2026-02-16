"""
Severity-Weighted Constraint Violations
Rates violation severity by how far they exceed hard limits
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ViolationSeverity:
    violation: str
    severity_pct: float  # How far over the limit (0-100+ percent)
    weight: float  # 1.0 (minor) to 4.0 (critical)
    impact_description: str


CONSTRAINT_LIMITS = {
    "leverage_ratio": 10.0,
    "proposed_loss": -10_000.0,
    "temperature": 0.0,
    "pressure": 0.0,
    "energy_in_vs_out": 0.0,  # Special case: energy_out - energy_in
}


def calculate_violation_severity(
    violation_name: str,
    actual_value: float,
    limit_value: Optional[float] = None,
) -> ViolationSeverity:
    """
    Score a constraint violation by severity.
    
    Logic:
    - severity_pct = (|actual - limit| / limit) × 100%
    - weight scales by severity:
        <25%: 1.0 (minor)
        25-100%: 2.0 (medium)
        >100%: 4.0 (critical)
    """
    if limit_value is None:
        limit_value = CONSTRAINT_LIMITS.get(violation_name, 0.0)
    
    if limit_value == 0.0:
        # For zero-based limits (temp, pressure), use absolute value
        overage = abs(actual_value)
        severity_pct = overage * 100  # Arbitrary scale for absolute values
    else:
        overage = abs(actual_value - limit_value)
        severity_pct = (overage / abs(limit_value)) * 100
    
    # Determine weight based on severity
    if severity_pct < 25:
        weight = 1.0
        impact = "Minor"
    elif severity_pct < 100:
        weight = 2.0
        impact = "Medium"
    else:
        weight = 4.0
        impact = "Critical"
    
    description = f"{impact} violation: {severity_pct:.1f}% over limit (actual={actual_value}, limit={limit_value})"
    
    return ViolationSeverity(
        violation=violation_name,
        severity_pct=severity_pct,
        weight=weight,
        impact_description=description,
    )


def calculate_overall_severity_score(violations: list[ViolationSeverity]) -> float:
    """
    Aggregate severity scores across all violations.
    
    Score = (sum of weights) / (number of violations)
    Range: 1.0 (minor) to 4.0 (critical)
    """
    if not violations:
        return 0.0
    return sum(v.weight for v in violations) / len(violations)
