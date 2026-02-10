from typing import List, Dict
import math
import re


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


def hallucination_divergence(responses: List[str]) -> float:
    """
    Measures mathematical divergence between three responses using
    pairwise Jensen-Shannon Divergence (JSD) over token distributions.
    Returns a score in [0.0, 1.0].
    """
    if len(responses) != 3:
        raise ValueError("hallucination_divergence expects exactly 3 responses")

    token_lists = [_tokenize(r) for r in responses]
    token_counts = [len(tokens) for tokens in token_lists]

    if sum(token_counts) == 0:
        return 0.0

    if any(count == 0 for count in token_counts) and any(count > 0 for count in token_counts):
        return 1.0

    vocab = sorted({token for tokens in token_lists for token in tokens})
    distributions = [_to_distribution(tokens, vocab) for tokens in token_lists]

    pairs = [(0, 1), (0, 2), (1, 2)]
    jsd_values = [
        _js_divergence(distributions[i], distributions[j]) for i, j in pairs
    ]

    return sum(jsd_values) / len(jsd_values)


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
