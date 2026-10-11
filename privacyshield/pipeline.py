"""Public orchestration API used by the UI, tests, and demo builders."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from .detectors import detect_words
from .document_io import load_document
from .models import Detection, Document
from .policies import apply_policy, load_policy
from .redaction import export_png, export_raster_pdf, redact_pages


DEFAULT_POLICY = Path(__file__).resolve().parents[1] / "configs" / "demo_policies.yaml"


def analyze(
    data: bytes,
    source_name: str,
    audience: str,
    custom_terms: Mapping[str, Sequence[str]] | None = None,
    policy_path: str | Path = DEFAULT_POLICY,
) -> tuple[Document, list[Detection]]:
    document = load_document(data, source_name)
    words = [word for page in document.pages for word in page.words]
    detections = detect_words(words, custom_terms)
    return document, apply_policy(detections, audience, load_policy(policy_path))


def export(document: Document, detections: list[Detection]) -> tuple[bytes, str, str]:
    images = redact_pages(document, detections)
    if document.source_kind == "image" and len(images) == 1:
        return export_png(images[0]), "image/png", "redacted.png"
    return export_raster_pdf(images), "application/pdf", "redacted.pdf"
