"""Streamlit interface for PrivacyShield."""

from __future__ import annotations

import hashlib
from pathlib import Path

import streamlit as st

from privacyshield.document_io import DocumentError
from privacyshield.pipeline import analyze, export
from privacyshield.redaction import redact_pages


st.set_page_config(page_title="PrivacyShield", page_icon="🛡️", layout="wide")

st.title("PrivacyShield")
st.caption("Audience-aware, local-first redaction before you share")
st.info(
    "Files are processed in this local Streamlit process and are not sent to an external AI API. "
    "Demo policies and OCR can miss content—always review the preview before sharing."
)

with st.sidebar:
    st.header("Sharing policy")
    audience = st.radio("Who will receive this file?", ["Internal Team", "External Client", "Public"], index=1)
    project_terms = st.text_input("Internal project names", "Project ORION")
    client_terms = st.text_input("Client names", "ACME HEALTH")
    st.caption("Comma-separate custom terms. Demo defaults are not a substitute for enterprise policy.")

upload = st.file_uploader("Upload a PNG, JPG, or text/scanned PDF (max 20 MB, 10 pages)", type=["png", "jpg", "jpeg", "pdf"])

if upload is None:
    st.markdown("Try the synthetic files in `demo/` after running `python demo/make_synthetic_docs.py`.")
    st.stop()

data = upload.getvalue()
custom_terms = {
    "internal_project": [term.strip() for term in project_terms.split(",")],
    "client_name": [term.strip() for term in client_terms.split(",")],
}

try:
    document, detections = analyze(data, upload.name, audience, custom_terms)
except DocumentError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.exception(exc)
    st.stop()

for warning in document.warnings:
    st.warning(warning)
if not detections:
    st.warning("No sensitive fields were detected. This does not prove that the document is safe.")

rows = [
    {
        "Redact": item.selected,
        "Page": item.page + 1,
        "Type": item.kind,
        "Detected text": item.text,
        "Action": item.action,
        "Reason": item.reason,
        "Confidence": round(item.confidence, 2),
    }
    for item in detections
]
st.subheader(f"Review {len(rows)} findings")
edited = st.data_editor(
    rows,
    disabled=["Page", "Type", "Detected text", "Action", "Reason", "Confidence"],
    hide_index=True,
    use_container_width=True,
    key=f"review-{hashlib.sha256(data).hexdigest()[:12]}-{audience}",
)
for item, row in zip(detections, edited):
    item.selected = bool(row["Redact"])

preview = redact_pages(document, detections)
left, right = st.columns(2)
with left:
    st.subheader("Original")
    for index, page in enumerate(document.pages):
        st.image(page.image, caption=f"Page {index + 1}", use_container_width=True)
with right:
    st.subheader("Redacted preview")
    for index, page in enumerate(preview):
        st.image(page, caption=f"Page {index + 1} · {audience}", use_container_width=True)

output, mime, default_name = export(document, detections)
stem = Path(upload.name).stem
suffix = ".png" if mime == "image/png" else ".pdf"
st.download_button(
    "Download irreversible redacted copy",
    data=output,
    file_name=f"{stem}_redacted{suffix}",
    mime=mime,
    type="primary",
)
st.caption("Export is rebuilt from redacted pixels; original PDF text objects, annotations, and metadata are not copied.")
