from typing import List, Dict
import math
import re
import numpy as np
from sentence_transformers import SentenceTransformer


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


def hallucination_divergence(responses: List[str]) -> float:
    """
    Measures mathematical divergence between three responses using
    semantic embeddings (all-MiniLM-L6-v2) and pairwise cosine distance.
    Returns a score in [0.0, 1.0].
    """
    if len(responses) != 3:
        raise ValueError("hallucination_divergence expects exactly 3 responses")

    if all(not r.strip() for r in responses):
        return 0.0

    if any(not r.strip() for r in responses) and any(r.strip() for r in responses):
        return 1.0

    model = _get_embedding_model()
    embeddings = model.encode(responses, normalize_embeddings=True)

    cos_01 = float(np.dot(embeddings[0], embeddings[1]))
    cos_02 = float(np.dot(embeddings[0], embeddings[2]))
    cos_12 = float(np.dot(embeddings[1], embeddings[2]))

    avg_cos = (cos_01 + cos_02 + cos_12) / 3.0
    score = (1.0 - avg_cos) / 2.0
    return float(min(max(score, 0.0), 1.0))


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9']+", text.lower())


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
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBEDDING_MODEL
