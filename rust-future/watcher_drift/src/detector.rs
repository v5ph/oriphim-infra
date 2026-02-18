use serde::{Deserialize, Serialize};

/// Result of drift detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DriftResult {
    pub detected: bool,
    pub z_score: f32,
    pub historical_mean: f32,
    pub current_value: f32,
    pub explanation: String,
}

/// Detects anomalies in streaming data using z-score
pub struct DriftDetector {
    data: Vec<f32>,
}

impl DriftDetector {
    pub fn new(historical_data: &[f32]) -> Self {
        DriftDetector {
            data: historical_data.to_vec(),
        }
    }

    /// Detect drift using z-score method
    /// Returns true if |z_score| > threshold (default 2.5)
    pub fn detect(&self, current_value: f32, threshold: f32) -> DriftResult {
        if self.data.len() < 5 {
            return DriftResult {
                detected: false,
                z_score: 0.0,
                historical_mean: 0.0,
                current_value,
                explanation: "Insufficient history for drift detection".to_string(),
            };
        }

        let (mean, std_dev) = self.compute_stats();

        if std_dev == 0.0 {
            return DriftResult {
                detected: false,
                z_score: 0.0,
                historical_mean: mean,
                current_value,
                explanation: "No variation in historical data".to_string(),
            };
        }

        let z_score = (current_value - mean) / std_dev;
        let detected = z_score.abs() > threshold;

        let explanation = if detected {
            format!(
                "Drift detected! Z-score={:.2} (current={:.3}, historical_mean={:.3}). \
                 Model behavior has shifted significantly.",
                z_score, current_value, mean
            )
        } else {
            format!(
                "Within normal range. Z-score={:.2}. Model behavior is stable (mean={:.3}).",
                z_score, mean
            )
        };

        DriftResult {
            detected,
            z_score,
            historical_mean: mean,
            current_value,
            explanation,
        }
    }

    /// Compute mean and standard deviation (single pass, numerically stable)
    fn compute_stats(&self) -> (f32, f32) {
        if self.data.is_empty() {
            return (0.0, 0.0);
        }

        let n = self.data.len() as f32;
        
        // Welford's online algorithm for mean
        let mean = self.data.iter().sum::<f32>() / n;

        // Compute variance
        let variance = self
            .data
            .iter()
            .map(|x| (x - mean).powi(2))
            .sum::<f32>()
            / n;

        let std_dev = variance.sqrt();

        (mean, std_dev)
    }
}

/// Compute z-score directly
pub fn compute_z_score(value: f32, mean: f32, std_dev: f32) -> f32 {
    if std_dev == 0.0 {
        0.0
    } else {
        (value - mean) / std_dev
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_drift_detection_normal() {
        let data = vec![0.1, 0.12, 0.11, 0.13, 0.12];
        let detector = DriftDetector::new(&data);
        let result = detector.detect(0.115, 2.5);
        assert!(!result.detected);
    }

    #[test]
    fn test_drift_detection_anomaly() {
        let data = vec![0.1, 0.12, 0.11, 0.13, 0.12];
        let detector = DriftDetector::new(&data);
        let result = detector.detect(0.5, 2.5);
        assert!(result.detected);
    }

    #[test]
    fn test_insufficient_history() {
        let data = vec![0.1, 0.2, 0.3];
        let detector = DriftDetector::new(&data);
        let result = detector.detect(0.25, 2.5);
        assert!(!result.detected);
    }
}
