from __future__ import annotations

from typing import List


EU_AI_ACT_ARTICLES = {
    "Conservation of Energy violated": "EU-AIA-12-RecordKeeping",
    "Temperature below absolute zero": "EU-AIA-12-RecordKeeping",
    "Negative pressure is invalid for this model": "EU-AIA-12-RecordKeeping",
    "Leverage ratio exceeds hard limit": "EU-AIA-14-HumanOversight",
    "VaR loss threshold exceeded": "EU-AIA-14-HumanOversight",
}

CA_SB243_ARTICLES = {
    "Leverage ratio exceeds hard limit": "CA-SB243-FinancialSafety",
    "VaR loss threshold exceeded": "CA-SB243-FinancialSafety",
}


DEFAULT_ARTICLES = ["EU-AIA-12-RecordKeeping", "CA-SB243-Transparency"]


def map_violations_to_articles(violations: List[str]) -> List[str]:
    articles: List[str] = []
    for violation in violations:
        if violation in EU_AI_ACT_ARTICLES:
            articles.append(EU_AI_ACT_ARTICLES[violation])
        if violation in CA_SB243_ARTICLES:
            articles.append(CA_SB243_ARTICLES[violation])
    if not articles:
        articles.extend(DEFAULT_ARTICLES)
    return sorted(set(articles))
