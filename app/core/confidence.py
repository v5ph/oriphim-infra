"""
Advanced Confidence Scoring
Quantifies uncertainty instead of binary pass/fail
"""

from dataclasses import dataclass


@dataclass
class ConfidenceScore:
    score: float  # 0.0 to 1.0
    risk_level: str  # "GREEN", "YELLOW", "RED"
    explanation: str


def calculate_confidence(divergence: float, violations: list[str]) -> ConfidenceScore:
    """
    Map divergence and violations to a confidence score.
    
    Logic:
    - Divergence alone: score = 1.0 - divergence
    - Each violation: subtract 0.15
    - Risk levels:
        GREEN (0.8+): Safe to execute
        YELLOW (0.5-0.8): Caution advised, review recommended
        RED (<0.5): DO NOT EXECUTE
    """
    threshold = 0.4
    confidence = 1.0 - divergence
    
    # Penalize for each violation
    violation_penalty = len(violations) * 0.15
    confidence = max(0.0, confidence - violation_penalty)
    
    # Determine risk level
    if confidence >= 0.8:
        risk_level = "GREEN"
        explanation = "High confidence. Safe to execute."
    elif confidence >= 0.5:
        risk_level = "YELLOW"
        explanation = "Moderate confidence. Manual review recommended."
    else:
        risk_level = "RED"
        explanation = "Low confidence. DO NOT EXECUTE."
    
    return ConfidenceScore(
        score=round(confidence, 3),
        risk_level=risk_level,
        explanation=explanation,
    )
