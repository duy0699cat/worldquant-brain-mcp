"""Reference-oriented tool helpers."""

from __future__ import annotations

from typing import Any

from ..reference.index import ReferenceIndex


def search_reference(index: ReferenceIndex, query: str, *, limit: int = 5) -> dict[str, Any]:
    matches = index.search(query, limit=limit)
    return {
        "query": query,
        "matches": matches,
        "match_count": len(matches),
    }


def list_reference_operators(index: ReferenceIndex, *, limit: int | None = None) -> dict[str, Any]:
    operators = index.list_operator_names()
    if limit is not None:
        operators = operators[:limit]
    return {
        "count": len(operators),
        "operators": operators,
    }
