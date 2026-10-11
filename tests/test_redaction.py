from io import BytesIO

import fitz
from PIL import Image

from privacyshield.models import Detection, Document, Page
from privacyshield.redaction import export_raster_pdf, redact_pages


def test_pixels_are_replaced_opaquely():
    image = Image.new("RGB", (200, 100), "white")
    document = Document([Page(image)], "test.png", "image")
    finding = Detection("email", "a@example.com", (20, 20, 180, 60), 0, 1.0, "test", selected=True)
    output = redact_pages(document, [finding])[0]
    assert output.getpixel((25, 25)) == (17, 24, 39)


def test_raster_pdf_has_no_text_layer_or_source_metadata():
    data = export_raster_pdf([Image.new("RGB", (300, 200), "white")])
    pdf = fitz.open(stream=BytesIO(data), filetype="pdf")
    assert "secret@example.com" not in "".join(page.get_text() for page in pdf)
    assert pdf.metadata.get("author") == "PrivacyShield"
