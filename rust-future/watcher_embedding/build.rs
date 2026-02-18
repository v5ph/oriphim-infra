use std::path::PathBuf;

fn main() {
    // This build script downloads the ONNX model on first build
    // The `ort` crate handles downloading and caching automatically
    
    // We can specify a custom cache directory if needed:
    // std::env::set_var("ORT_MODELS", PathBuf::from("."));
    
    println!("cargo:warning=Building watcher_embedding with ONNX support");
}
