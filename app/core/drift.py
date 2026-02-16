"""
Drift Detection & Historical Pattern Analysis
Detects when LLM behavior degrades or changes significantly
"""

from dataclasses import dataclass, field
from collections import deque
from typing import Optional
import statistics


@dataclass
class DriftAlert:
    detected: bool
    z_score: float
    historical_mean: float
    current_value: float
    explanation: str


class RequestHistory:
    """In-memory circular buffer for tracking LLM behavior patterns."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.divergence_history = deque(maxlen=window_size)
        self.violation_counts = deque(maxlen=window_size)

    def record(self, divergence: float, violation_count: int):
        """Record a validation result."""
        self.divergence_history.append(divergence)
        self.violation_counts.append(violation_count)

    def get_stats(self):
        """Return mean and std dev of recent history."""
        if len(self.divergence_history) < 2:
            return {"mean": 0.0, "std_dev": 0.0, "count": len(self.divergence_history)}

        mean = statistics.mean(self.divergence_history)
        std_dev = statistics.stdev(self.divergence_history)
        return {"mean": mean, "std_dev": std_dev, "count": len(self.divergence_history)}

    def detect_drift(self, current_divergence: float) -> DriftAlert:
        """
        Detect if current divergence is anomalous.
        
        Logic:
        - Z-score = (current - mean) / std_dev
        - If |z_score| > 2.5: DRIFT DETECTED
        - This means current value is >2.5 standard deviations from normal
        """
        stats = self.get_stats()

        if stats["count"] < 5:  # Not enough history
            return DriftAlert(
                detected=False,
                z_score=0.0,
                historical_mean=stats["mean"],
                current_value=current_divergence,
                explanation="Insufficient history for drift detection",
            )

        mean = stats["mean"]
        std_dev = stats["std_dev"]

        if std_dev == 0:  # No variation in history
            return DriftAlert(
                detected=False,
                z_score=0.0,
                historical_mean=mean,
                current_value=current_divergence,
                explanation="No variation in historical data",
            )

        z_score = (current_divergence - mean) / std_dev
        detected = abs(z_score) > 2.5

        if detected:
            explanation = (
                f"Drift detected! Z-score={z_score:.2f} (current={current_divergence:.3f}, "
                f"historical_mean={mean:.3f}). Model behavior has shifted significantly."
            )
        else:
            explanation = (
                f"Within normal range. Z-score={z_score:.2f}. "
                f"Model behavior is stable (mean={mean:.3f})."
            )

        return DriftAlert(
            detected=detected,
            z_score=z_score,
            historical_mean=mean,
            current_value=current_divergence,
            explanation=explanation,
        )


# Global history tracker
request_history = RequestHistory(window_size=100)
