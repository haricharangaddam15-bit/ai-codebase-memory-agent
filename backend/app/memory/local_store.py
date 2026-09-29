from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalMemoryStore:
    """
    Development memory store.

    This is intentionally deterministic and evidence-first.
    Hindsight will replace this persistence layer later.
    """

    def __init__(self, path: str = "data/memory/memories.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, memories: list[dict[str, Any]]) -> None:
        payload = {
            "version": 1,
            "memory_count": len(memories),
            "memories": memories,
        }

        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload.get("memories", [])

    def search(self, query: str) -> list[dict[str, Any]]:
        memories = self.load()

        terms = {
            term.lower()
            for term in query.split()
            if len(term.strip()) >= 3
        }

        scored: list[tuple[int, dict[str, Any]]] = []

        for memory in memories:
            searchable = " ".join(
                [
                    str(memory.get("title", "")),
                    str(memory.get("summary", "")),
                    str(memory.get("rationale", "")),
                    str(memory.get("module", "")),
                    " ".join(memory.get("file_paths", [])),
                ]
            ).lower()

            score = sum(1 for term in terms if term in searchable)

            if score > 0:
                scored.append((score, memory))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [memory for _, memory in scored]
