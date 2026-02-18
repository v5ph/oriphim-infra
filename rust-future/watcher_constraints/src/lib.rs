mod executor;
mod parser;

pub use executor::{check_logic, ConstraintError, ValidationRequest};
pub use parser::parse_constraints;

use pyo3::prelude::*;

/// Python wrapper for constraint validation
#[pyfunction]
fn validate_constraints(
    physics_energy_in: Option<f32>,
    physics_energy_out: Option<f32>,
    financial_proposed_loss: Option<f32>,
    metrics: Option<std::collections::HashMap<String, f32>>,
) -> PyResult<Vec<String>> {
    let request = ValidationRequest {
        physics_energy_in,
        physics_energy_out,
        financial_proposed_loss,
        metrics: metrics.unwrap_or_default(),
    };

    executor::check_logic(&request)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

#[pymodule]
fn watcher_constraints(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_constraints, m)?)?;
    Ok(())
}
