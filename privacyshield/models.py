"""Small, serializable data models shared by the pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from PIL import Image


@dataclass(frozen=True)
class Word:
    text: str
    bbox: tuple[float, float, float, float]
    page: int
    line_id: str
    confidence: float = 1.0


@dataclass
class Detection:
    kind: str
    text: str
    bbox: tuple[float, float, float, float]
    page: int
    confidence: float
    detector: str
    action: str = "review"
    reason: str = "Needs human review"
    selected: bool = True

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bbox"] = [round(v, 2) for v in self.bbox]
        return data


@dataclass
class Page:
    image: Image.Image
    words: list[Word] = field(default_factory=list)


@dataclass
class Document:
    pages: list[Page]
    source_name: str
    source_kind: str
    warnings: list[str] = field(default_factory=list)
