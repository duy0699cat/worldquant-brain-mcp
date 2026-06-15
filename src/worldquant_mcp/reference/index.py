"""Keyword search over locally extracted WorldQuant reference chunks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TOKEN_PATTERN = re.compile(r"[a-z0-9_]{2,}")


@dataclass(frozen=True)
class ReferenceChunk:
    id: str
    source: str
    page: int
    chunk: int
    text: str
    operators: tuple[str, ...]


class ReferenceIndex:
    def __init__(self, chunks: list[ReferenceChunk], markdown: str = ""):
        self.chunks = chunks
        self.markdown = markdown

    @classmethod
    def load(cls, chunks_path: Path, markdown_path: Path | None = None) -> "ReferenceIndex":
        chunks: list[ReferenceChunk] = []
        markdown = ""

        if chunks_path.exists():
            raw_data = json.loads(chunks_path.read_text(encoding="utf-8"))
            for item in raw_data:
                chunks.append(
                    ReferenceChunk(
                        id=item["id"],
                        source=item["source"],
                        page=int(item["page"]),
                        chunk=int(item["chunk"]),
                        text=item["text"],
                        operators=tuple(item.get("operators", [])),
                    )
                )

        if markdown_path and markdown_path.exists():
            markdown = markdown_path.read_text(encoding="utf-8")

        return cls(chunks=chunks, markdown=markdown)

    def search(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        tokens = set(TOKEN_PATTERN.findall(query.lower()))
        if not tokens:
            return []

        scored: list[tuple[int, ReferenceChunk]] = []
        for chunk in self.chunks:
            lowered = chunk.text.lower()
            score = 0
            for token in tokens:
                score += lowered.count(token)
                if token in chunk.operators:
                    score += 3
            if score:
                scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1].page, item[1].chunk))
        return [
            {
                "id": chunk.id,
                "source": chunk.source,
                "page": chunk.page,
                "chunk": chunk.chunk,
                "operators": list(chunk.operators),
                "score": score,
                "text": chunk.text,
            }
            for score, chunk in scored[:limit]
        ]

    def list_operator_names(self) -> list[str]:
        names = {operator for chunk in self.chunks for operator in chunk.operators}
        return sorted(names)
