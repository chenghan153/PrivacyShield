"""Irreversible pixel-level redaction and safe export."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from .models import Detection, Document


def _font(size: int = 14) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def redact_pages(document: Document, detections: list[Detection]) -> list[Image.Image]:
    """Return copied page images with opaque boxes burned into pixels."""
    outputs = [page.image.copy().convert("RGB") for page in document.pages]
    for item in detections:
        if not item.selected:
            continue
        image = outputs[item.page]
        draw = ImageDraw.Draw(image)
        margin = 3
        x0, y0, x1, y1 = item.bbox
        box = (max(0, x0 - margin), max(0, y0 - margin), min(image.width, x1 + margin), min(image.height, y1 + margin))
        draw.rectangle(box, fill=(17, 24, 39))
        label = item.kind.upper().replace("_", " ")
        font = _font(max(9, min(15, int((box[3] - box[1]) * 0.55))))
        label_box = draw.textbbox((0, 0), label, font=font)
        if label_box[2] <= box[2] - box[0] - 6 and label_box[3] <= box[3] - box[1] - 2:
            draw.text((box[0] + 3, box[1] + 1), label, font=font, fill=(255, 255, 255))
    return outputs


def export_png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def export_raster_pdf(images: list[Image.Image], dpi: int = 150) -> bytes:
    """Build a fresh image-only PDF with sanitized metadata.

    The original PDF objects, text layer, annotations, and metadata are never
    copied into the output.
    """
    if not images:
        raise ValueError("At least one page is required")
    converted = [image.convert("RGB") for image in images]
    buffer = BytesIO()
    converted[0].save(
        buffer,
        format="PDF",
        save_all=True,
        append_images=converted[1:],
        resolution=float(dpi),
        title="PrivacyShield redacted export",
        author="PrivacyShield",
        subject="Rasterized redacted document",
        keywords="redacted",
    )
    return buffer.getvalue()
