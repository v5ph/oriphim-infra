mod embedding;
mod model;

pub use embedding::{compute_divergence, EmbeddingError};
pub use model::EmbeddingModel;

use pyo3::prelude::*;

/// Python wrapper for Rust embedding engine
#[pyfunction]
fn compute_embeddings(
    samples: Vec<String>,
) -> PyResult<Vec<Vec<f32>>> {
    embedding::encode_batch(&samples)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

/// Python wrapper for divergence computation
#[pyfunction]
fn compute_divergence_pyo3(
    samples: Vec<String>,
) -> PyResult<f32> {
    compute_divergence(&samples)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
}

#[pymodule]
fn watcher_embedding(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_embeddings, m)?)?;
    m.add_function(wrap_pyfunction!(compute_divergence_pyo3, m)?)?;
    Ok(())
}
