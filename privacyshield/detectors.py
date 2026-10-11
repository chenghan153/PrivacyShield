"""Deterministic sensitive-text detectors with word-box projection."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence

from .models import Detection, Word


PATTERNS: dict[str, re.Pattern[str]] = {
    "api_key": re.compile(
        r"(?i)(?:api[_ -]?key|secret|token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{12,})|\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{10,}\b"
    ),
    "email": re.compile(r"(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b"),
    "phone": re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?)?\d{3,4}[\s.\-]\d{3,4}(?!\w)"),
    "national_id": re.compile(r"(?i)\b[A-Z][12]\d{8}\b"),
    "financial": re.compile(r"(?i)(?:cost|margin|salary|bank|account|budget)\s*[:=]\s*(?:USD|NTD|\$)?\s*[\d,]+(?:\.\d+)?%?"),
}


def _union_box(words: Sequence[Word]) -> tuple[float, float, float, float]:
    return (
        min(w.bbox[0] for w in words),
        min(w.bbox[1] for w in words),
        max(w.bbox[2] for w in words),
        max(w.bbox[3] for w in words),
    )


def _line_text(words: Sequence[Word]) -> tuple[str, list[tuple[int, int, Word]]]:
    chunks: list[str] = []
    spans: list[tuple[int, int, Word]] = []
    cursor = 0
    for word in words:
        if chunks:
            chunks.append(" ")
            cursor += 1
        start = cursor
        chunks.append(word.text)
        cursor += len(word.text)
        spans.append((start, cursor, word))
    return "".join(chunks), spans


def _matches_to_detections(
    words: Sequence[Word], kind: str, pattern: re.Pattern[str], detector: str
) -> list[Detection]:
    text, spans = _line_text(words)
    found: list[Detection] = []
    for match in pattern.finditer(text):
        selected_words = [word for start, end, word in spans if start < match.end() and end > match.start()]
        if not selected_words:
            continue
        value = match.group(0).strip(" \t,;.")
        confidence = min(word.confidence for word in selected_words)
        found.append(
            Detection(
                kind=kind,
                text=value,
                bbox=_union_box(selected_words),
                page=selected_words[0].page,
                confidence=confidence,
                detector=detector,
            )
        )
    return found


def detect_words(
    words: Iterable[Word], custom_terms: Mapping[str, Sequence[str]] | None = None
) -> list[Detection]:
    """Detect sensitive values in positioned words.

    Matching is line-oriented so multi-token values retain a precise bounding
    box. Custom terms are escaped and therefore treated as literal strings.
    """
    by_line: dict[tuple[int, str], list[Word]] = defaultdict(list)
    for word in words:
        if word.text.strip():
            by_line[(word.page, word.line_id)].append(word)

    detections: list[Detection] = []
    for line_words in by_line.values():
        ordered = sorted(line_words, key=lambda item: (item.bbox[1], item.bbox[0]))
        for kind, pattern in PATTERNS.items():
            detections.extend(_matches_to_detections(ordered, kind, pattern, "regex"))
        for kind, terms in (custom_terms or {}).items():
            clean = [term.strip() for term in terms if term.strip()]
            if not clean:
                continue
            pattern = re.compile("|".join(re.escape(term) for term in sorted(clean, key=len, reverse=True)), re.I)
            detections.extend(_matches_to_detections(ordered, kind, pattern, "custom dictionary"))

    # Prefer one record per type/text/box; overlapping types remain visible for review.
    unique: dict[tuple[object, ...], Detection] = {}
    for item in detections:
        key = (item.page, item.kind, item.text.lower(), *(round(v, 1) for v in item.bbox))
        unique[key] = item
    return sorted(unique.values(), key=lambda item: (item.page, item.bbox[1], item.bbox[0], item.kind))


def detect_text(text: str, custom_terms: Mapping[str, Sequence[str]] | None = None) -> list[tuple[str, str]]:
    """Text-only convenience detector used for evaluation."""
    hits: list[tuple[str, str]] = []
    for kind, pattern in PATTERNS.items():
        hits.extend((kind, match.group(0)) for match in pattern.finditer(text))
    for kind, terms in (custom_terms or {}).items():
        for term in terms:
            if term and re.search(re.escape(term), text, re.I):
                hits.append((kind, term))
    return hits
