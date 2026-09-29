from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "did",
    "do",
    "does",
    "for",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "the",
    "to",
    "we",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "was",
    "were",
    "would",
    "choose",
    "chosen",
    "select",
    "selected",
    "decision",
    "decided",
    "because",
    "reason",
    "reasons",
    "use",
    "used",
    "using",
}


def normalize_source_url(value: str) -> str:
    value = str(value or "").strip()

    markdown_match = re.fullmatch(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        value,
    )

    if markdown_match:
        return markdown_match.group(2)

    return value


def tokenize(value: str) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9._-]*", value.lower())

    return [
        word
        for word in words
        if word not in STOPWORDS and len(word) >= 3
    ]


class LocalMemoryStore:
    """
    Deterministic development memory store.

    This store is intentionally evidence-first:
    memories without evidence are never returned.
    """

    def __init__(self, path: str):
        self.path = Path(path)

    def save(self, memories: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        normalized_memories = []

        for memory in memories:
            copied = dict(memory)

            evidence = dict(copied.get("evidence", {}))

            if evidence.get("source_url"):
                evidence["source_url"] = normalize_source_url(
                    evidence["source_url"]
                )

            copied["evidence"] = evidence
            normalized_memories.append(copied)

        payload = {
            "version": 1,
            "memory_count": len(normalized_memories),
            "memories": normalized_memories,
        }

        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        payload = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        memories = payload.get("memories", [])

        return [
            memory
            for memory in memories
            if memory.get("evidence", {}).get("quote", "").strip()
        ]

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query_terms = set(tokenize(query))

        if not query_terms:
            return []

        scored: list[tuple[int, int, dict[str, Any]]] = []

        for memory in self.load():
            title = str(memory.get("title", ""))
            summary = str(memory.get("summary", ""))
            rationale = str(memory.get("rationale", ""))
            module = str(memory.get("module", ""))
            file_paths = " ".join(
                memory.get("file_paths", [])
            )

            searchable_fields = {
                "title": set(tokenize(title)),
                "summary": set(tokenize(summary)),
                "rationale": set(tokenize(rationale)),
                "module": set(tokenize(module)),
                "file_paths": set(tokenize(file_paths)),
            }

            matched_terms = set()

            for terms in searchable_fields.values():
                matched_terms.update(query_terms & terms)

            if not matched_terms:
                continue

            # Strong matches on title/module/file paths are more
            # meaningful than generic matches in the rationale.
            title_matches = len(
                query_terms & searchable_fields["title"]
            )
            module_matches = len(
                query_terms & searchable_fields["module"]
            )
            file_matches = len(
                query_terms & searchable_fields["file_paths"]
            )

            score = (
                len(matched_terms)
                + title_matches * 5
                + module_matches * 3
                + file_matches * 3
            )

            # Require at least one meaningful query term to occur
            # in the identity of the memory when the query contains
            # a specific technology/entity.
            identity_matches = (
                query_terms
                & (
                    searchable_fields["title"]
                    | searchable_fields["module"]
                    | searchable_fields["file_paths"]
                )
            )

            if not identity_matches:
                continue

            scored.append(
                (
                    score,
                    len(matched_terms),
                    memory,
                )
            )

        scored.sort(
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )

        return [
            memory
            for _, _, memory in scored[:limit]
        ]
