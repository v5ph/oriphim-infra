"""
Drift Detection & Historical Pattern Analysis
Detects when LLM behavior degrades or changes significantly

LATENCY OPTIMIZATION: Uses Welford's algorithm for O(1) incremental mean/variance
instead of storing rolling window for O(n) recomputation each request.
"""

from collections import deque
from dataclasses import dataclass
from typing import Optional
import statistics


@dataclass
class DriftAlert:
    detected: bool
    z_score: float
    historical_mean: float
    current_value: float
    explanation: str


class IncrementalStats:
    """Welford's online algorithm for mean/variance in O(1) space and time.
    
    Instead of: deque(maxlen=100) recomputing stdev each time
    Use: M_n and M2_n tracking for O(1) updates
    """
    
    def __init__(self):
        self.count = 0
        self.mean = 0.0
        self.M2 = 0.0  # Running sum of squares of differences
    
    def update(self, value: float):
        """Add new value using Welford's algorithm. O(1) time."""
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.M2 += delta * delta2
    
    def get_stats(self) -> dict:
        """Return mean and sample std_dev."""
        if self.count < 2:
            return {"mean": self.mean, "std_dev": 0.0, "count": self.count}
        variance = self.M2 / (self.count - 1)
        std_dev = variance ** 0.5
        return {"mean": self.mean, "std_dev": std_dev, "count": self.count}
    
    def to_dict(self) -> dict:
        """Serialize state for persistence (prevents count type issues)."""
        return {
            "count": int(self.count),  # Ensure integer serialization
            "mean": float(self.mean),
            "M2": float(self.M2)
        }
    
    @classmethod
    def from_dict(cls, state: dict) -> 'IncrementalStats':
        """Deserialize state from persistence."""
        instance = cls()
        instance.count = int(state.get("count", 0))  # Type-safe deserialization
        instance.mean = float(state.get("mean", 0.0))
        instance.M2 = float(state.get("M2", 0.0))
        return instance


class RequestHistory:
    """In-memory drift tracker using Welford's algorithm for O(1) updates."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.stats = IncrementalStats()
        self.violation_counts = deque(maxlen=window_size)

    def record(self, divergence: float, violation_count: int):
        """Record a validation result. O(1) time."""
        self.stats.update(divergence)
        self.violation_counts.append(violation_count)

    def get_stats(self):
        """Return mean and std dev of all history."""
        return self.stats.get_stats()

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

        if std_dev <= 0:  # No variation in history (0 or invalid)
            return DriftAlert(
                detected=False,
                z_score=0.0,
                historical_mean=mean,
                current_value=current_divergence,
                explanation="Cannot compute z-score: zero or negative std_dev (no variation in historical data)",
            )

        z_score = (current_divergence - mean) / std_dev  # Protected by std_dev > 0 check above
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
