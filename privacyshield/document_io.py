"""Local-only image/PDF ingestion and positioned text extraction."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError
from pytesseract import Output

from .models import Document, Page, Word


SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg"}
SUPPORTED_PDFS = {".pdf"}
MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 10


class DocumentError(ValueError):
    pass


def _ocr_words(image: Image.Image, page_number: int) -> list[Word]:
    try:
        data = pytesseract.image_to_data(image, output_type=Output.DICT, config="--psm 6")
    except pytesseract.TesseractNotFoundError as exc:
        raise DocumentError("Tesseract is not installed or not available on PATH") from exc
    except pytesseract.TesseractError as exc:
        raise DocumentError(
            "Tesseract OCR could not start. Run scripts/setup.sh to install local English OCR data."
        ) from exc
    words: list[Word] = []
    for index, raw in enumerate(data["text"]):
        text = raw.strip()
        if not text:
            continue
        confidence = max(0.0, float(data["conf"][index])) / 100.0
        left, top = float(data["left"][index]), float(data["top"][index])
        width, height = float(data["width"][index]), float(data["height"][index])
        line_id = f"{data['block_num'][index]}:{data['par_num'][index]}:{data['line_num'][index]}"
        words.append(Word(text, (left, top, left + width, top + height), page_number, line_id, confidence))
    return words


def _open_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise DocumentError("The uploaded file is not a valid PNG or JPEG image") from exc
    image = ImageOps.exif_transpose(image).convert("RGB")
    if image.width * image.height > 40_000_000:
        raise DocumentError("Image is too large; maximum decoded size is 40 megapixels")
    return image


def _load_pdf(data: bytes, source_name: str, dpi: int) -> Document:
    try:
        pdf = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise DocumentError("The uploaded PDF is invalid or encrypted") from exc
    if pdf.needs_pass:
        pdf.close()
        raise DocumentError("Password-protected PDFs are not supported")
    if pdf.page_count == 0:
        pdf.close()
        raise DocumentError("The PDF contains no pages")
    if pdf.page_count > MAX_PAGES:
        pdf.close()
        raise DocumentError(f"PDF has {pdf.page_count} pages; the demo limit is {MAX_PAGES}")

    scale = dpi / 72.0
    pages: list[Page] = []
    warnings: list[str] = []
    try:
        for page_number, pdf_page in enumerate(pdf):
            pix = pdf_page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            raw_words = pdf_page.get_text("words", sort=True)
            words: list[Word] = []
            for item in raw_words:
                x0, y0, x1, y1, text, block, line, _word = item[:8]
                words.append(
                    Word(
                        str(text),
                        (x0 * scale, y0 * scale, x1 * scale, y1 * scale),
                        page_number,
                        f"{block}:{line}",
                        1.0,
                    )
                )
            if not words:
                words = _ocr_words(image, page_number)
                warnings.append(f"Page {page_number + 1} had no text layer; local OCR was used.")
            pages.append(Page(image=image, words=words))
    finally:
        pdf.close()
    return Document(pages, source_name, "pdf", warnings)


def load_document(data: bytes, source_name: str, dpi: int = 150) -> Document:
    """Load supported bytes without writing the upload to disk."""
    if not data:
        raise DocumentError("The uploaded file is empty")
    if len(data) > MAX_BYTES:
        raise DocumentError(f"File exceeds the {MAX_BYTES // (1024 * 1024)} MB demo limit")
    suffix = Path(source_name).suffix.lower()
    if suffix in SUPPORTED_IMAGES:
        image = _open_image(data)
        words = _ocr_words(image, 0)
        warning = [] if words else ["OCR found no text. Do not treat this output as verified safe."]
        return Document([Page(image=image, words=words)], source_name, "image", warning)
    if suffix in SUPPORTED_PDFS:
        return _load_pdf(data, source_name, dpi)
    raise DocumentError("Unsupported file type. Upload PNG, JPG, JPEG, or PDF.")
