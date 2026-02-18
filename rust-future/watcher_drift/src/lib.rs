use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

mod detector;

pub use detector::{compute_z_score, DriftDetector, DriftResult};

/// Python wrapper for drift detection
#[pyfunction]
fn detect_drift(
    historical_data: Vec<f32>,
    current_value: f32,
    threshold: Option<f32>,
) -> PyResult<(bool, f32, f32, f32, String)> {
    let threshold = threshold.unwrap_or(2.5);
    let detector = DriftDetector::new(&historical_data);
    let result = detector.detect(current_value, threshold);

    Ok((
        result.detected,
        result.z_score,
        result.historical_mean,
        result.current_value,
        result.explanation,
    ))
}

#[pymodule]
fn watcher_drift(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(detect_drift, m)?)?;
    Ok(())
}
