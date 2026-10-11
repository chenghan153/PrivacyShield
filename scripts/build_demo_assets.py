#!/usr/bin/env python3
"""Generate actual engine outputs and scripted UI-style demo frames."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from privacyshield.pipeline import analyze
from privacyshield.redaction import redact_pages


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "demo" / "synthetic_dashboard.png"
OUT = ROOT / "demo" / "outputs"
CUSTOM = {"internal_project": ["Project ORION"], "client_name": ["ACME HEALTH"]}


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "#eef2f7")
    canvas.paste(copy, ((size[0] - copy.width) // 2, (size[1] - copy.height) // 2))
    return canvas


def ui_frame(original: Image.Image, redacted: Image.Image, audience: str, findings: int, selected: int) -> Image.Image:
    frame = Image.new("RGB", (1600, 900), "#f8fafc")
    draw = ImageDraw.Draw(frame)
    draw.rectangle((0, 0, 1600, 78), fill="#102a43")
    draw.text((45, 19), "PrivacyShield", font=font(32, True), fill="white")
    draw.text((1240, 26), "LOCAL PROCESSING", font=font(18, True), fill="#66e3c4")
    draw.rounded_rectangle((40, 105, 1560, 855), radius=18, fill="white", outline="#cbd5e1", width=2)
    draw.text((75, 130), f"Audience: {audience}", font=font(24, True), fill="#102a43")
    draw.text((75, 172), f"{findings} findings · {selected} selected for redaction", font=font(17), fill="#475569")
    before = contain(original, (680, 560))
    after = contain(redacted, (680, 560))
    frame.paste(before, (75, 235))
    frame.paste(after, (845, 235))
    draw.text((75, 205), "ORIGINAL", font=font(17, True), fill="#64748b")
    draw.text((845, 205), "IRREVERSIBLE PREVIEW", font=font(17, True), fill="#64748b")
    draw.text((1120, 825), "Scripted capture · actual engine output", font=font(14), fill="#64748b")
    return frame


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = INPUT.read_bytes()
    original = Image.open(INPUT).convert("RGB")
    for audience in ("Internal Team", "External Client", "Public"):
        document, findings = analyze(data, INPUT.name, audience, CUSTOM)
        output = redact_pages(document, findings)[0]
        slug = audience.lower().replace(" ", "_")
        output.save(OUT / f"{slug}_redacted.png", optimize=True)
        frame = ui_frame(original, output, audience, len(findings), sum(item.selected for item in findings))
        frame.save(OUT / f"{slug}_ui.png", optimize=True)
        print(audience, len(findings), sum(item.selected for item in findings))


if __name__ == "__main__":
    main()
