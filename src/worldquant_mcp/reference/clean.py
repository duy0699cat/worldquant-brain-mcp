"""Utilities for turning noisy PDF text into retrieval-friendly markdown."""

from __future__ import annotations

import re


HEADING_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9 /,&()\-]{2,}$")
OPERATOR_PATTERN = re.compile(r"\b([a-z]+(?:_[a-z0-9]+)*)\s*\(")


def normalize_whitespace(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r", "").split("\n")]
    cleaned: list[str] = []
    previous_blank = False

    for raw_line in lines:
        line = re.sub(r"\s+", " ", raw_line).strip()

        if not line:
            if not previous_blank and cleaned:
                cleaned.append("")
            previous_blank = True
            continue

        cleaned.append(line)
        previous_blank = False

    return "\n".join(cleaned).strip()


def looks_like_heading(line: str) -> bool:
    if len(line) > 100:
        return False
    if line.count(" ") > 10:
        return False
    return bool(HEADING_PATTERN.match(line))


def clean_page_text(page_text: str) -> str:
    normalized = normalize_whitespace(page_text)
    lines = normalized.split("\n")
    markdown_lines: list[str] = []

    for line in lines:
        if looks_like_heading(line):
            markdown_lines.append(f"## {line.title()}")
            continue

        if line.startswith(("•", "- ", "* ")):
            bullet = line[1:].strip() if line[0] == "•" else line[2:].strip()
            markdown_lines.append(f"- {bullet}")
            continue

        if "`" not in line and any(token in line for token in ("ts_", "group_", "trade_when", "rank(")):
            markdown_lines.append(f"`{line}`")
            continue

        markdown_lines.append(line)

    return "\n".join(markdown_lines).strip()


def extract_operator_names(text: str) -> list[str]:
    names = {match.group(1) for match in OPERATOR_PATTERN.finditer(text)}
    return sorted(names)


def split_into_chunks(text: str, *, chunk_size: int = 1400) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)

    return chunks
