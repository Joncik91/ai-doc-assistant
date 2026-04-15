"""Document format extractors."""

from __future__ import annotations

import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


@dataclass(slots=True)
class ExtractedPage:
    """Text extracted from a single page or logical section."""

    page_number: int | None
    text: str
    section: str | None = None


@dataclass(slots=True)
class ExtractionResult:
    """Structured extraction output."""

    text: str
    pages: list[ExtractedPage]
    warnings: list[str] = field(default_factory=list)
    content_type: str = "text/plain"


def _guess_content_type(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(path.name)
    return content_type or "application/octet-stream"


def _normalize_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_document(path: Path) -> ExtractionResult:
    """Extract text and metadata from a supported file."""

    extension = path.suffix.lower()
    if extension in {".txt", ".md", ".markdown"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        normalized = _normalize_text(text)
        return ExtractionResult(
            text=normalized,
            pages=[ExtractedPage(page_number=1, text=normalized)],
            content_type=_guess_content_type(path),
        )

    if extension == ".pdf":
        reader = PdfReader(str(path))
        pages: list[ExtractedPage] = []
        warnings: list[str] = []
        page_texts: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            normalized = _normalize_text(text)
            if not normalized:
                warnings.append(f"Page {index} did not contain extractable text.")
            pages.append(ExtractedPage(page_number=index, text=normalized))
            if normalized:
                page_texts.append(normalized)
        return ExtractionResult(
            text=_normalize_text("\n\n".join(page_texts)),
            pages=pages,
            warnings=warnings,
            content_type=_guess_content_type(path),
        )

    if extension == ".docx":
        document = DocxDocument(str(path))
        paragraphs: list[str] = []
        current_section: str | None = None
        pages: list[ExtractedPage] = []
        current_page = 1
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            style_name = getattr(paragraph.style, "name", "") or ""
            if style_name.lower().startswith("heading"):
                current_section = text
                continue
            paragraphs.append(text)
            pages.append(ExtractedPage(page_number=current_page, text=text, section=current_section))
        normalized = _normalize_text("\n\n".join(paragraphs))
        if not pages and normalized:
            pages = [ExtractedPage(page_number=1, text=normalized)]
        return ExtractionResult(
            text=normalized,
            pages=pages,
            content_type=_guess_content_type(path),
        )

    raise ValueError(f"Unsupported file type: {path.suffix}")

