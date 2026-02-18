use crate::model::{get_model, EmbeddingError};
use ndarray::Array2;
use std::f32;

/// Compute the semantic divergence between three text samples
/// using embedding-based cosine similarity.
///
/// Returns a score in [0.0, 1.0]:
/// - 0.0 = all samples identical
/// - 1.0 = all samples completely different
pub fn compute_divergence(samples: &[String]) -> Result<f32, EmbeddingError> {
    if samples.len() != 3 {
        return Err(EmbeddingError::EncodingError(
            "Expected exactly 3 samples".to_string(),
        ));
    }

    // Check for empty samples
    if samples.iter().all(|s| s.trim().is_empty()) {
        return Ok(0.0);
    }

    if samples
        .iter()
        .any(|s| s.trim().is_empty() && samples.iter().any(|s2| !s2.trim().is_empty()))
    {
        return Ok(1.0);
    }

    // Get embeddings
    let refs: Vec<&str> = samples.iter().map(|s| s.as_str()).collect();
    let embeddings = encode_batch(&samples)?;

    // Compute pairwise cosine similarities
    let cos_01 = cosine_similarity(&embeddings[0], &embeddings[1]);
    let cos_02 = cosine_similarity(&embeddings[0], &embeddings[2]);
    let cos_12 = cosine_similarity(&embeddings[1], &embeddings[2]);

    // Average cosine similarity
    let avg_cos = (cos_01 + cos_02 + cos_12) / 3.0;

    // Convert similarity to divergence
    // divergence = (1 - similarity) / 2
    let divergence = (1.0 - avg_cos) / 2.0;

    Ok(divergence.max(0.0).min(1.0))
}

/// Encode a batch of text samples into embeddings
pub fn encode_batch(samples: &[String]) -> Result<Vec<Vec<f32>>, EmbeddingError> {
    let model = get_model()?;
    let refs: Vec<&str> = samples.iter().map(|s| s.as_str()).collect();
    model.encode(&refs)
}

/// Compute cosine similarity between two embedding vectors
/// Uses normalized dot product (vectors should be L2 normalized)
#[inline]
fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.is_empty() || b.is_empty() || a.len() != b.len() {
        return 0.0;
    }

    // For already-normalized embeddings, cosine similarity is just dot product
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cosine_similarity_identical() {
        let v1 = vec![1.0, 0.0, 0.0];
        let v2 = vec![1.0, 0.0, 0.0];
        assert!((cosine_similarity(&v1, &v2) - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_cosine_similarity_orthogonal() {
        let v1 = vec![1.0, 0.0, 0.0];
        let v2 = vec![0.0, 1.0, 0.0];
        assert!((cosine_similarity(&v1, &v2)).abs() < 0.001);
    }

    #[test]
    fn test_cosine_similarity_opposite() {
        let v1 = vec![1.0, 0.0, 0.0];
        let v2 = vec![-1.0, 0.0, 0.0];
        assert!((cosine_similarity(&v1, &v2) + 1.0).abs() < 0.001);
    }
}
