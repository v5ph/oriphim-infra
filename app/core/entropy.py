from typing import List, Dict
import math
import os
import re
import threading
from collections import OrderedDict
import numpy as np
from sentence_transformers import SentenceTransformer


_EMBEDDING_LOCK = threading.Lock()  # Thread-safe cache access


def semantic_entropy(samples: List[str]) -> float:
    if not samples:
        return 0.0

    counts = {}
    for sample in samples:
        key = sample.strip().lower()
        counts[key] = counts.get(key, 0) + 1

    total = len(samples)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log(p, 2)

    max_entropy = math.log(total, 2) if total > 1 else 1.0
    return min(entropy / max_entropy, 1.0)


_EMBEDDING_MODEL: SentenceTransformer | None = None
_EMBEDDING_CACHE: OrderedDict = OrderedDict()  # LRU cache: text -> embedding
_CACHE_MAX_SIZE = 1000


def _embeddings_disabled() -> bool:
    return os.getenv("ORIPHIM_DISABLE_EMBEDDINGS", "false").lower() == "true"


def _lexical_divergence(responses: List[str]) -> float:
    vocab = sorted({token for response in responses for token in _tokenize(response)})
    if not vocab:
        return 0.0

    distributions = [_to_distribution(_tokenize(response), vocab) for response in responses]
    divergences = [
        _js_divergence(distributions[0], distributions[1]),
        _js_divergence(distributions[0], distributions[2]),
        _js_divergence(distributions[1], distributions[2]),
    ]
    return float(min(max(sum(divergences) / len(divergences), 0.0), 1.0))


def hallucination_divergence(responses: List[str]) -> float:
    """
    Measures mathematical divergence between three responses using
    semantic embeddings (all-MiniLM-L6-v2) and pairwise cosine distance.
    Returns a score in [0.0, 1.0].
    
    LATENCY OPTIMIZATIONS:
    1. Pre-warm model at startup (load_embedding_model)
    2. Cache embeddings per request_id to avoid re-computing
    3. Cap sample count at 3 (input validation)
    """
    if len(responses) != 3:
        raise ValueError(f"hallucination_divergence expects exactly 3 responses, got {len(responses)}")

    if all(not r.strip() for r in responses):
        return 0.0

    if any(not r.strip() for r in responses) and any(r.strip() for r in responses):
        return 1.0

    if _embeddings_disabled():
        return _lexical_divergence(responses)

    try:
        model = _get_embedding_model()
        embeddings = _get_cached_embeddings(responses, model)
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Falling back to lexical divergence because embedding model is unavailable", exc_info=True)
        return _lexical_divergence(responses)

    cos_01 = float(np.dot(embeddings[0], embeddings[1]))
    cos_02 = float(np.dot(embeddings[0], embeddings[2]))
    cos_12 = float(np.dot(embeddings[1], embeddings[2]))

    avg_cos = (cos_01 + cos_02 + cos_12) / 3.0
    score = (1.0 - avg_cos) / 2.0
    
    # Clamp to [0, 1] and log if clamping occurs (indicates calculation issue)
    clamped_score = float(min(max(score, 0.0), 1.0))
    if clamped_score != score:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Entropy score clamped from {score:.4f} to {clamped_score:.4f}. "
            f"Indicates potential calculation issue. cos_01={cos_01:.4f}, cos_02={cos_02:.4f}, cos_12={cos_12:.4f}"
        )
    return clamped_score


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9']+", text.lower())


def clear_embedding_cache() -> None:
    """Clear embedding cache (for memory pressure or session boundaries)."""
    global _EMBEDDING_CACHE
    _EMBEDDING_CACHE.clear()


def _to_distribution(tokens: List[str], vocab: List[str]) -> Dict[str, float]:
    counts: Dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1

    total = len(tokens)
    if total == 0:
        return {term: 0.0 for term in vocab}

    return {term: counts.get(term, 0) / total for term in vocab}


def _js_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    m = {term: (p[term] + q[term]) / 2 for term in p}
    return 0.5 * _kl_divergence(p, m) + 0.5 * _kl_divergence(q, m)


def _kl_divergence(p: Dict[str, float], m: Dict[str, float]) -> float:
    total = 0.0
    for term, p_i in p.items():
        if p_i == 0:
            continue
        m_i = m[term]
        total += p_i * math.log(p_i / m_i, 2)
    return total


def _get_embedding_model() -> SentenceTransformer:
    """Get or load the embedding model (lazy init or pre-warmed)."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBEDDING_MODEL


def load_embedding_model() -> None:
    """Pre-warm embedding model at startup to avoid cold start latency.
    
    Call this during application startup to download and cache the model.
    Prevents first request timeout when model is downloaded on-demand.
    """
    global _EMBEDDING_MODEL
    if _embeddings_disabled():
        return
    if _EMBEDDING_MODEL is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Pre-warming embedding model (all-MiniLM-L6-v2)...")
        _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded successfully")


def _get_cached_embeddings(responses: List[str], model: SentenceTransformer) -> np.ndarray:
    """Retrieve embeddings from cache or compute and cache them.
    
    Cache strategy:
    - Hit: Return cached embedding (O(1) lookup under lock)
    - Miss: Compute batch, cache results, enforce max size
    - LRU eviction: When cache exceeds 1000 entries, remove oldest
    """
    embeddings_list = []
    uncached = []
    uncached_indices = []
    
    # First pass: check cache (thread-safe)
    with _EMBEDDING_LOCK:
        for i, response in enumerate(responses):
            response_clean = response.strip()
            if response_clean in _EMBEDDING_CACHE:
                embeddings_list.append(_EMBEDDING_CACHE[response_clean])
                # Mark as recently used by moving to end
                _EMBEDDING_CACHE.move_to_end(response_clean)
            else:
                embeddings_list.append(None)
                uncached.append(response_clean)
                uncached_indices.append(i)
    
    # Compute uncached embeddings in batch
    if uncached:
        batch_embeddings = model.encode(uncached, normalize_embeddings=True)
        with _EMBEDDING_LOCK:
            for idx, text, embedding in zip(uncached_indices, uncached, batch_embeddings):
                embeddings_list[idx] = embedding
                # LRU eviction: remove oldest entry when cache exceeds max size
                if len(_EMBEDDING_CACHE) >= _CACHE_MAX_SIZE:
                    _EMBEDDING_CACHE.popitem(last=False)  # Remove oldest (FIFO in OrderedDict)
                _EMBEDDING_CACHE[text] = embedding
                # Move to end (mark as recently used)
                _EMBEDDING_CACHE.move_to_end(text)
    
    return np.array(embeddings_list)
