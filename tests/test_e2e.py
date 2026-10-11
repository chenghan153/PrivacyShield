from io import BytesIO
from pathlib import Path

import fitz

from privacyshield.pipeline import analyze, export


CUSTOM = {"internal_project": ["Project ORION"], "client_name": ["ACME HEALTH"]}


def test_pdf_end_to_end_is_rasterized(synthetic_pdf):
    document, findings = analyze(synthetic_pdf, "synthetic.pdf", "Public", CUSTOM)
    kinds = {item.kind for item in findings}
    assert {"email", "phone", "api_key", "internal_project", "client_name", "financial"} <= kinds
    assert all(item.selected for item in findings)
    output, mime, filename = export(document, findings)
    assert mime == "application/pdf"
    assert filename.endswith(".pdf")
    redacted = fitz.open(stream=BytesIO(output), filetype="pdf")
    assert not "".join(page.get_text() for page in redacted)
    assert b"alex@example.com" not in output
    assert b"sk_test_51DEMOONLY987654321" not in output


def test_same_document_changes_with_audience(synthetic_pdf):
    _, internal = analyze(synthetic_pdf, "synthetic.pdf", "Internal Team", CUSTOM)
    _, public = analyze(synthetic_pdf, "synthetic.pdf", "Public", CUSTOM)
    internal_selected = {(item.kind, item.text) for item in internal if item.selected}
    public_selected = {(item.kind, item.text) for item in public if item.selected}
    assert internal_selected < public_selected


def test_png_ocr_end_to_end():
    path = Path(__file__).parents[1] / "demo" / "synthetic_dashboard.png"
    document, findings = analyze(path.read_bytes(), path.name, "Public", CUSTOM)
    kinds = {item.kind for item in findings}
    assert document.source_kind == "image"
    assert {"email", "phone", "api_key", "internal_project", "client_name", "financial"} <= kinds
