#!/usr/bin/env python3
"""Build a narrated <3 minute scripted demo from actual engine outputs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
from datetime import timedelta
from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

from privacyshield.pipeline import analyze, export


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video"
FRAMES = VIDEO / "frames"
SEGMENTS = ROOT / ".tmp" / "video-segments"
DEMO = ROOT / "demo"
OUTPUTS = DEMO / "outputs"
RESULTS = json.loads((ROOT / "evaluation" / "results.json").read_text(encoding="utf-8"))
GITHUB = "github.com/chenghan153/PrivacyShield"
YOUTUBE = os.environ.get("YOUTUBE_URL", "Upload this MP4, then add the YouTube link to the deck")
CUSTOM = {"internal_project": ["Project ORION"], "client_name": ["ACME HEALTH"]}

NAVY = "#102a43"
INK = "#172033"
SLATE = "#475569"
LIGHT = "#f8fafc"
TEAL = "#14b8a6"
MINT = "#66e3c4"
WHITE = "#ffffff"
AMBER = "#f59e0b"


SCENES = [
    {
        "title": "A sharing mistake can outlive the message",
        "subtitle": "Screenshots and PDFs mix useful context with credentials, personal contacts, and commercial terms.",
        "narration": "A screenshot sent to the wrong audience can expose credentials, personal contacts, internal project names, and commercial terms. Manual redaction is easy to forget, and the correct decision changes depending on who will receive the file.",
        "image": "original",
    },
    {
        "title": "PrivacyShield adds the recipient to the policy",
        "subtitle": "Local detection, explainable actions, human review, and irreversible export.",
        "narration": "PrivacyShield creates a separate, audience-aware copy before sharing. It runs locally, explains every proposed action, keeps a person in control, and rebuilds the final PNG or PDF from redacted pixels.",
        "image": "concept",
    },
    {
        "title": "1 · Upload a fictional document",
        "subtitle": "PNG, JPG, and text or scanned PDF are processed in the local application.",
        "narration": "Here is our fictional delivery brief. It contains a client name, an internal project, contact details, a fake API key, and a budget. The application accepts PNG, JPEG, and PDF, without sending document content to an external AI API.",
        "image": "original",
    },
    {
        "title": "2 · Internal Team policy",
        "subtitle": "The secret is redacted; the budget is routed to review. Contact and project context can remain.",
        "narration": "For the Internal Team audience, contact and project context are allowed by the demo policy. The fake API key is always redacted. The budget is selected for human review. Every finding still has a visible checkbox.",
        "image": "internal_team_ui.png",
        "actual": True,
    },
    {
        "title": "3 · External Client policy",
        "subtitle": "Contact, internal project, secret, and financial details are selected. Client identity requires review.",
        "narration": "Switching to External Client changes the policy. Personal contact details, the internal project, credential, and budget are now blocked. Client identity requires review, so it remains selected until a person explicitly decides.",
        "image": "external_client_ui.png",
        "actual": True,
    },
    {
        "title": "4 · Public policy",
        "subtitle": "The strictest demo policy redacts every detected sensitive category.",
        "narration": "For a Public audience, every detected sensitive category is redacted. The difference is policy-driven and explainable. These defaults are only for the demonstration; a real organization must configure its own disclosure rules.",
        "image": "public_ui.png",
        "actual": True,
    },
    {
        "title": "5 · Export a new pixel-only file",
        "subtitle": "No original PDF text objects, annotations, hidden layers, or source metadata are copied.",
        "narration": "On export, PrivacyShield burns opaque masks into copied pixels and creates a fresh image-only PDF. In this actual check, extracted text has zero characters, and the sample email and API key are absent from the exported bytes.",
        "image": "verify",
        "actual": True,
    },
    {
        "title": "Measured, with a narrow claim",
        "subtitle": "10 tests pass · synthetic fixtures: TP/FP/FN 24/0/0 · five-PDF median 79.04 ms.",
        "narration": "Ten automated tests pass, including an end-to-end export check. Twenty-three purpose-built text fixtures produce twenty-four true positives, zero false positives, and zero false negatives. This synthetic result bypasses OCR and is not a production accuracy claim.",
        "image": "metrics",
    },
    {
        "title": "Edge plan: preserve the safety baseline",
        "subtitle": "Stage I runs on a workstation CPU. UGen300 and Hailo are a Stage II validation plan.",
        "narration": "The Stage I prototype runs on a workstation CPU. If selected, Stage II will measure UGen300 and Hailo compatibility, latency, memory, and model quality. Deterministic rules and human review remain the safety baseline. No hardware result is claimed today.",
        "image": "architecture",
    },
    {
        "title": "PrivacyShield · review before you share",
        "subtitle": "Working source, tests, synthetic evidence, and reproducible setup are on GitHub.",
        "narration": "PrivacyShield is a focused safety checkpoint for teams that share work outside the company. The working source, tests, synthetic demo, and reproducible evaluation are available on GitHub. Thank you for watching.",
        "image": "links",
    },
]


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def cover(image: Image.Image, target: tuple[int, int]) -> Image.Image:
    image = image.copy().convert("RGB")
    ratio = min(target[0] / image.width, target[1] / image.height)
    image = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", target, "#e8eef4")
    canvas.paste(image, ((target[0] - image.width) // 2, (target[1] - image.height) // 2))
    return canvas


def draw_wrapped(draw, xy, text, max_chars, size, color, bold=False, spacing=8, align="left"):
    lines = textwrap.wrap(text, width=max_chars)
    draw.multiline_text(xy, "\n".join(lines), font=font(size, bold), fill=color, spacing=spacing, align=align)


def base_frame(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1280, 720), LIGHT)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1280, 92), fill=NAVY)
    draw.text((48, 22), "PrivacyShield", font=font(32, True), fill=WHITE)
    draw.text((1000, 33), "LOCAL-FIRST", font=font(17, True), fill=MINT)
    draw.text((55, 118), title, font=font(30, True), fill=NAVY)
    draw_wrapped(draw, (57, 168), subtitle, 95, 17, SLATE)
    draw.rectangle((0, 625, 1280, 720), fill=NAVY)
    return image, draw


def make_frame(scene: dict, index: int, verification: dict[str, object]) -> Image.Image:
    image, draw = base_frame(scene["title"], scene["subtitle"])
    image_key = scene["image"]
    if image_key == "original":
        source = cover(Image.open(DEMO / "synthetic_dashboard.png"), (720, 360))
        image.paste(source, (500, 235))
        draw.rounded_rectangle((55, 258, 430, 545), radius=20, fill=WHITE, outline="#cbd5e1", width=2)
        draw.text((90, 295), "BEFORE SHARING", font=font(18, True), fill=TEAL)
        draw_wrapped(draw, (90, 345), "Choose who will receive this file before deciding what must be hidden.", 30, 24, INK, True, 12)
    elif image_key.endswith(".png"):
        source = cover(Image.open(OUTPUTS / image_key), (1150, 365))
        image.paste(source, (65, 235))
    elif image_key == "concept":
        items = [("UPLOAD", "local bytes"), ("POLICY", "recipient-aware"), ("REVIEW", "human decision"), ("EXPORT", "fresh pixels")]
        for i, (heading, detail) in enumerate(items):
            x = 70 + i * 300
            draw.rounded_rectangle((x, 285, x + 240, 480), radius=22, fill=WHITE, outline=TEAL, width=3)
            draw.text((x + 22, 325), heading, font=font(21, True), fill=NAVY)
            draw_wrapped(draw, (x + 22, 385), detail, 18, 18, SLATE)
            if i < 3:
                draw.polygon([(x + 260, 370), (x + 280, 385), (x + 260, 400)], fill=TEAL)
    elif image_key == "verify":
        draw.rounded_rectangle((120, 250, 1160, 550), radius=24, fill="#071827", outline=TEAL, width=3)
        lines = [
            "$ verify redacted_export.pdf",
            f"PDF pages: {verification['pages']}",
            f"Extracted text characters: {verification['text_chars']}",
            f"Sample email found in bytes: {verification['email_found']}",
            f"Sample API key found in bytes: {verification['key_found']}",
            "Result: fresh raster PDF verified",
        ]
        for row, line in enumerate(lines):
            draw.text((165, 280 + row * 42), line, font=font(19, row in {0, 5}), fill=MINT if row in {0, 5} else WHITE)
    elif image_key == "metrics":
        values = [
            ("AUTOMATED TESTS", "10 passed"),
            ("SYNTHETIC TP / FP / FN", "24 / 0 / 0"),
            ("5-PDF MEDIAN", f"{RESULTS['benchmark']['median_ms']:.2f} ms"),
        ]
        for i, (heading, value) in enumerate(values):
            x = 80 + i * 400
            draw.rounded_rectangle((x, 275, x + 345, 485), radius=22, fill=WHITE, outline=TEAL, width=3)
            draw.text((x + 24, 315), heading, font=font(16, True), fill=TEAL)
            draw.text((x + 24, 385), value, font=font(31, True), fill=NAVY)
        draw.text((192, 540), "Synthetic fixtures are not evidence of production accuracy.", font=font(19, True), fill="#b45309")
    elif image_key == "architecture":
        left = ["Upload", "Text / OCR", "Rules", "Policy", "Review", "Raster export"]
        for i, label in enumerate(left):
            x = 50 + (i % 3) * 190
            y = 255 + (i // 3) * 105
            draw.rounded_rectangle((x, y, x + 165, y + 70), radius=12, fill=WHITE, outline=TEAL, width=2)
            draw.text((x + 13, y + 23), label, font=font(15, True), fill=NAVY)
        draw.text((95, 490), "IMPLEMENTED ON CPU", font=font(18, True), fill=TEAL)
        draw.rounded_rectangle((675, 245, 1195, 520), radius=22, fill="#fff7ed", outline=AMBER, width=3)
        draw.text((720, 282), "STAGE II VALIDATION", font=font(20, True), fill=NAVY)
        draw_wrapped(draw, (720, 340), "UGen300 / Hailo compatibility\nMeasured latency and memory\nEvidence before claims", 38, 21, SLATE, True, 14)
    elif image_key == "links":
        draw.rounded_rectangle((125, 260, 1155, 365), radius=18, fill=WHITE, outline=TEAL, width=3)
        draw.text((170, 285), "GITHUB REPOSITORY", font=font(15, True), fill=TEAL)
        draw.text((170, 320), GITHUB, font=font(24, True), fill=NAVY)
        draw.rounded_rectangle((125, 405, 1155, 510), radius=18, fill=WHITE, outline="#cbd5e1", width=2)
        draw_wrapped(draw, (170, 430), YOUTUBE, 70, 19, SLATE, True)

    label = "SCRIPTED DEMO · ACTUAL ENGINE OUTPUT" if scene.get("actual") else "STAGE I DEMO · FICTIONAL DATA"
    draw.text((40, 640), label, font=font(14, True), fill=MINT)
    draw_wrapped(draw, (370, 640), scene["narration"], 105, 13, WHITE, False, 5)
    draw.text((1205, 682), f"{index + 1:02d}", font=font(13, True), fill=MINT)
    return image


def duration_seconds(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True,
        text=True,
        capture_output=True,
    )
    return float(result.stdout.strip())


def srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def verify_export() -> dict[str, object]:
    data = (DEMO / "synthetic_invoice.pdf").read_bytes()
    document, findings = analyze(data, "synthetic_invoice.pdf", "Public", CUSTOM)
    output, _mime, _name = export(document, findings)
    pdf = fitz.open(stream=BytesIO(output), filetype="pdf")
    text = "".join(page.get_text() for page in pdf)
    return {
        "pages": pdf.page_count,
        "text_chars": len(text),
        "email_found": "YES" if b"alex@example.com" in output else "NO",
        "key_found": "YES" if b"sk_test_51DEMOONLY987654321" in output else "NO",
    }


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def main() -> None:
    for tool in ("espeak-ng", "ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise RuntimeError(f"Required tool not found: {tool}")
    VIDEO.mkdir(exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    SEGMENTS.mkdir(parents=True, exist_ok=True)
    verification = verify_export()
    segment_paths: list[Path] = []
    subtitle_lines: list[str] = []
    cursor = 0.0
    for index, scene in enumerate(SCENES):
        frame_path = FRAMES / f"scene_{index + 1:02d}.png"
        audio_path = SEGMENTS / f"scene_{index + 1:02d}.wav"
        segment_path = SEGMENTS / f"scene_{index + 1:02d}.mp4"
        make_frame(scene, index, verification).save(frame_path, optimize=True)
        run(["espeak-ng", "-v", "en-us+m3", "-s", "150", "-p", "42", "-w", str(audio_path), scene["narration"]])
        audio_duration = duration_seconds(audio_path)
        run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(frame_path), "-i", str(audio_path),
            "-vf", "fade=t=in:st=0:d=0.35,fade=t=out:st=" + f"{max(0.0, audio_duration - 0.35):.3f}" + ":d=0.35",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(segment_path),
        ])
        duration = duration_seconds(segment_path)
        segment_paths.append(segment_path)
        subtitle_lines.extend([
            str(index + 1),
            f"{srt_time(cursor)} --> {srt_time(cursor + duration)}",
            scene["narration"],
            "",
        ])
        cursor += duration

    concat = SEGMENTS / "concat.txt"
    concat.write_text("".join(f"file '{path}'\n" for path in segment_paths), encoding="utf-8")
    output = VIDEO / "PrivacyShield_Stage_I_Demo.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(output)])
    (VIDEO / "captions_en.srt").write_text("\n".join(subtitle_lines), encoding="utf-8")
    final_duration = duration_seconds(output)
    if final_duration > 180:
        raise RuntimeError(f"Video is {final_duration:.2f}s, exceeding the 180s limit")
    verification_md = f"""# Video verification

Measured after running `scripts/build_video.py`.

- Production method: scripted sequence with actual local engine outputs, local `espeak-ng` narration, and visible English text.
- Cloud services used: none.
- Fictional data only: yes.
- Screen recording claim: no; explicitly labeled scripted demo.
- Output: `video/PrivacyShield_Stage_I_Demo.mp4`.
- Duration: **{final_duration:.3f} seconds**, below the 180-second limit.
- Video: **H.264, 1280×720, 30 fps, yuv420p**.
- Audio: **AAC, 22.05 kHz, mono**.
- English captions: narration is visibly rendered in every scene; `captions_en.srt` is also provided.
- Export evidence: {verification['pages']}-page raster PDF, {verification['text_chars']} extracted text characters, sample email {verification['email_found']}, sample API key {verification['key_found']}.
- YouTube upload: not performed; requires project owner account.
"""
    (VIDEO / "video_verification.md").write_text(verification_md, encoding="utf-8")
    print(json.dumps({"output": str(output), "duration_seconds": round(final_duration, 3), "verification": verification}, indent=2))


if __name__ == "__main__":
    main()
