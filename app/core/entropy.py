from typing import List
import math


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
