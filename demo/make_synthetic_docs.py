"""Generate fictional demo inputs. No real people, clients, or secrets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"


LINES = [
    ("QUARTERLY DELIVERY BRIEF", "heading"),
    ("SYNTHETIC DEMO DATA — NOT A REAL COMPANY", "muted"),
    ("Client: ACME HEALTH", "body"),
    ("Internal project: Project ORION", "body"),
    ("Owner: Alex Example", "body"),
    ("Email: alex@example.com", "body"),
    ("Phone: +886 912-345-678", "body"),
    ("API key: sk_test_51DEMOONLY987654321", "body"),
    ("Budget: USD 75,000", "body"),
    ("Status: Pilot approved for synthetic evaluation", "body"),
]


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def make_png(path: Path) -> None:
    image = Image.new("RGB", (1400, 900), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 55, 1330, 845), radius=28, fill="white", outline="#cbd5e1", width=3)
    draw.rectangle((70, 55, 1330, 170), fill="#102a43")
    y = 95
    for text, style in LINES:
        if style == "heading":
            draw.text((120, y), text, font=_font(38, True), fill="white")
            y = 205
        elif style == "muted":
            draw.text((120, y), text, font=_font(19, True), fill="#64748b")
            y += 70
        else:
            draw.text((120, y), text, font=_font(28), fill="#172033")
            y += 65
    image.save(path, optimize=True)


def make_pdf(path: Path) -> None:
    page_width, page_height = A4
    pdf = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    pdf.setTitle("Synthetic PrivacyShield Demo")
    pdf.setAuthor("PrivacyShield synthetic data generator")
    pdf.setFillColor(HexColor("#102a43"))
    pdf.rect(0, page_height - 120, page_width, 120, stroke=0, fill=1)
    y = page_height - 76
    for text, style in LINES:
        if style == "heading":
            pdf.setFillColor(HexColor("#ffffff"))
            pdf.setFont("Helvetica-Bold", 22)
            pdf.drawString(48, y, text)
            y = page_height - 160
        elif style == "muted":
            pdf.setFillColor(HexColor("#64748b"))
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(48, y, text)
            y -= 52
        else:
            pdf.setFillColor(HexColor("#172033"))
            pdf.setFont("Helvetica", 14)
            pdf.drawString(48, y, text)
            y -= 42
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColor(HexColor("#64748b"))
    pdf.drawString(48, 36, "Generated locally for demonstration. Every entity and credential is fictional.")
    pdf.showPage()
    pdf.save()


def main() -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    make_png(DEMO / "synthetic_dashboard.png")
    make_pdf(DEMO / "synthetic_invoice.pdf")
    print("Generated synthetic_dashboard.png and synthetic_invoice.pdf")


if __name__ == "__main__":
    main()
