from __future__ import annotations

import re

from sqlalchemy import and_, or_


STRICT_SUBJECT_SYNONYMS: dict[str, list[str]] = {
    "artificial-intelligence": ["ai", "artificial intelligence"],
    "computer-science": ["computer science", "computing", "cs"],
    "computer-networks": ["computer networks", "networking"],
    "cybersecurity": [
        "cybersecurity",
        "cyber security",
        "computer security",
        "information security",
    ],
    "data-structures": ["data structures", "data structure"],
    "differential-equations": [
        "differential equations",
        "ordinary differential equations",
        "partial differential equations",
    ],
    "discrete-mathematics": [
        "discrete mathematics",
        "discrete math",
        "discrete structures",
    ],
    "large-language-models": [
        "large language models",
        "large language model",
        "llm",
        "language models",
    ],
    "machine-learning": ["machine learning", "statistical learning"],
    "natural-language-processing": ["natural language processing", "nlp"],
    "operating-systems": ["operating systems", "operating system"],
    "probability": ["probability", "probability theory"],
    "proof-writing": [
        "proof writing",
        "proofs",
        "proof",
        "mathematical proofs",
        "logic and proof",
    ],
    "real-analysis": ["real analysis"],
    "software-engineering": ["software engineering"],
}


def normalize_subject_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9+#.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def strict_title_scope(title: str) -> str:
    return title.split(" | ", 1)[0]


def strict_subject_phrases(subject_slug: str) -> list[str]:
    fallback = subject_slug.replace("-", " ")
    seen: set[str] = set()
    phrases: list[str] = []
    for phrase in [fallback, *STRICT_SUBJECT_SYNONYMS.get(subject_slug, [])]:
        normalized = normalize_subject_text(phrase)
        if normalized and normalized not in seen:
            seen.add(normalized)
            phrases.append(normalized)
    return phrases


def phrase_matches(haystack: str, phrase: str) -> bool:
    normalized = normalize_subject_text(phrase)
    if not normalized:
        return False
    pattern = rf"(^|[^a-z0-9]){re.escape(normalized)}([^a-z0-9]|$)"
    return re.search(pattern, haystack) is not None


def strict_subject_matches_title(title: str, subject_slug: str) -> bool:
    scoped_title = normalize_subject_text(strict_title_scope(title))
    return any(
        phrase_matches(scoped_title, phrase)
        for phrase in strict_subject_phrases(subject_slug)
    )


def strict_subject_title_condition(title_column, subject_slug: str):
    conditions = []
    for phrase in strict_subject_phrases(subject_slug):
        pattern = f"%{phrase}%"
        suffix_pattern = f"% | %{phrase}%"
        conditions.append(
            and_(title_column.ilike(pattern), ~title_column.ilike(suffix_pattern))
        )
    return or_(*conditions)
