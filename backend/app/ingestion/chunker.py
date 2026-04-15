"""Chunking helpers for retrieved document text."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.ingestion.extractors import ExtractedPage


@dataclass(slots=True)
class ChunkCandidate:
    """Chunk ready for persistence or indexing."""

    chunk_index: int
    content: str
    page_number: int | None
    section: str | None
    start_char: int
    end_char: int
    source_label: str


def _split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def _split_long_paragraph(paragraph: str, max_chars: int, overlap: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    chunks: list[str] = []
    start = 0
    while start < len(paragraph):
        end = min(len(paragraph), start + max_chars)
        chunks.append(paragraph[start:end].strip())
        if end == len(paragraph):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def chunk_pages(
    pages: list[ExtractedPage],
    *,
    source_label: str,
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[ChunkCandidate]:
    """Chunk extracted pages while preserving source metadata."""

    chunks: list[ChunkCandidate] = []
    chunk_index = 0

    for page in pages:
        if not page.text.strip():
            continue

        paragraphs = _split_paragraphs(page.text) or [page.text.strip()]
        current_parts: list[str] = []
        current_length = 0
        current_start = 0

        def flush_current(end_char: int) -> None:
            nonlocal chunk_index, current_parts, current_length, current_start
            if not current_parts:
                return
            content = "\n\n".join(current_parts).strip()
            if content:
                chunks.append(
                    ChunkCandidate(
                        chunk_index=chunk_index,
                        content=content,
                        page_number=page.page_number,
                        section=page.section,
                        start_char=current_start,
                        end_char=end_char,
                        source_label=source_label,
                    )
                )
                chunk_index += 1
            current_parts = []
            current_length = 0
            current_start = end_char

        for paragraph in paragraphs:
            parts = _split_long_paragraph(paragraph, max_chars=max_chars, overlap=overlap)
            for part in parts:
                additional = len(part) + (2 if current_parts else 0)
                if current_parts and current_length + additional > max_chars:
                    flush_current(current_start + current_length)
                if current_parts:
                    current_length += 2
                current_parts.append(part)
                current_length += len(part)

        flush_current(current_start + current_length)

    return chunks
