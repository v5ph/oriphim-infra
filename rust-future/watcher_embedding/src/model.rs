use once_cell::sync::Lazy;
use ort::{Session, SessionBuilder, Value};
use std::env;
use std::path::PathBuf;
use thiserror::Error;
use tokenizers::Tokenizer;

/// Error types for embedding operations
#[derive(Error, Debug)]
pub enum EmbeddingError {
    #[error("ONNX Runtime error: {0}")]
    OrtError(String),
    
    #[error("Tokenizer error: {0}")]
    TokenizerError(String),
    
    #[error("Model initialization failed: {0}")]
    InitError(String),
    
    #[error("Encoding failed: {0}")]
    EncodingError(String),
}

/// Manages the embedding model lifecycle (load once, reuse)
pub struct EmbeddingModel {
    session: Session,
    tokenizer: Tokenizer,
}

// Global embedding model (lazy static, loaded once)
static EMBEDDING_MODEL: Lazy<Result<EmbeddingModel, EmbeddingError>> =
    Lazy::new(|| EmbeddingModel::new());

impl EmbeddingModel {
    /// Load the all-MiniLM-L6-v2 ONNX model
    /// Downloads from HuggingFace if not cached
    pub fn new() -> Result<Self, EmbeddingError> {
        // Try to load from local cache first, fall back to download
        let model_path = Self::get_model_path()?;
        
        let session = SessionBuilder::new()
            .with_execution_providers([ort::ExecutionProvider::cpu()])
            .map_err(|e| EmbeddingError::OrtError(e.to_string()))?
            .commit_from_file(&model_path)
            .map_err(|e| EmbeddingError::OrtError(e.to_string()))?;

        // Load tokenizer (all-MiniLM-L6-v2 uses standard BERT tokenizer)
        let tokenizer = Self::load_tokenizer()?;

        Ok(EmbeddingModel { session, tokenizer })
    }

    /// Get or create model path
    fn get_model_path() -> Result<PathBuf, EmbeddingError> {
        let cache_dir = env::var("WATCHER_MODEL_CACHE")
            .unwrap_or_else(|_| {
                dirs::cache_dir()
                    .unwrap_or_else(|| PathBuf::from("."))
                    .join("watcher_embeddings")
                    .to_string_lossy()
                    .to_string()
            });

        let model_path = PathBuf::from(&cache_dir).join("all-MiniLM-L6-v2.onnx");

        // For now, assume model exists or will be downloaded by ort
        // In production, implement proper download logic
        Ok(model_path)
    }

    /// Load BERT tokenizer (can be from local or embedded)
    fn load_tokenizer() -> Result<Tokenizer, EmbeddingError> {
        // Load from HuggingFace tokenizers library
        Tokenizer::from_pretrained("sentence-transformers/all-MiniLM-L6-v2", None)
            .map_err(|e| EmbeddingError::TokenizerError(e.to_string()))
    }

    /// Encode a batch of text samples
    pub fn encode(&self, texts: &[&str]) -> Result<Vec<Vec<f32>>, EmbeddingError> {
        let encodings = self
            .tokenizer
            .encode_batch(texts.to_vec(), true)
            .map_err(|e| EmbeddingError::TokenizerError(e.to_string()))?;

        let mut embeddings = Vec::new();

        for encoding in encodings {
            let input_ids: Vec<i64> = encoding
                .get_ids()
                .iter()
                .map(|&id| id as i64)
                .collect();

            let attention_mask: Vec<i64> = encoding
                .get_attention_mask()
                .iter()
                .map(|&m| m as i64)
                .collect();

            let token_type_ids: Vec<i64> = encoding
                .get_type_ids()
                .iter()
                .map(|&id| id as i64)
                .collect();

            // Prepare ONNX inputs
            let inputs = [
                Value::from_array_raw(
                    &[input_ids.len() as i64, 1],
                    &input_ids,
                )
                .map_err(|e| EmbeddingError::OrtError(e.to_string()))?,
                Value::from_array_raw(
                    &[attention_mask.len() as i64, 1],
                    &attention_mask,
                )
                .map_err(|e| EmbeddingError::OrtError(e.to_string()))?,
                Value::from_array_raw(
                    &[token_type_ids.len() as i64, 1],
                    &token_type_ids,
                )
                .map_err(|e| EmbeddingError::OrtError(e.to_string()))?,
            ];

            // Run inference
            let outputs = self
                .session
                .run(inputs.as_slice())
                .map_err(|e| EmbeddingError::OrtError(e.to_string()))?;

            // Extract embedding from outputs
            let embedding = Self::extract_embedding(&outputs)?;
            embeddings.push(embedding);
        }

        Ok(embeddings)
    }

    /// Extract the sentence embedding from model outputs
    fn extract_embedding(outputs: &[Value]) -> Result<Vec<f32>, EmbeddingError> {
        // all-MiniLM-L6-v2 outputs a tensor of shape [1, 384]
        // We extract and return as Vec<f32>
        if outputs.is_empty() {
            return Err(EmbeddingError::EncodingError(
                "No outputs from model".to_string(),
            ));
        }

        // Try to extract as f32 tensor
        outputs[0]
            .try_extract_tensor::<f32>()
            .map_err(|e| EmbeddingError::OrtError(e.to_string()))?
            .as_slice()
            .to_vec()
            // For single sample, reshape [1, 384] to [384]
            .ok()
            .ok_or_else(|| {
                EmbeddingError::EncodingError("Failed to extract tensor".to_string())
            })
    }
}

/// Get the global embedding model
pub fn get_model() -> Result<&'static EmbeddingModel, EmbeddingError> {
    EMBEDDING_MODEL.as_ref().map_err(|e| EmbeddingError::InitError(e.to_string()))
}
