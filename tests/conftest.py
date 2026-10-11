from __future__ import annotations

from io import BytesIO

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


@pytest.fixture()
def synthetic_pdf() -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    lines = [
        "Client: ACME HEALTH",
        "Internal project: Project ORION",
        "Email: alex@example.com",
        "Phone: +886 912-345-678",
        "API key: sk_test_51DEMOONLY987654321",
        "Budget: USD 75,000",
    ]
    y = 720
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 32
    pdf.save()
    return buffer.getvalue()
