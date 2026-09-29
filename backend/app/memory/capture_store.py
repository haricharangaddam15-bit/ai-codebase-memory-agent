from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CaptureStore:
    """
    Local persistence for pending/approved/rejected capture drafts.
    """

    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        payload = json.loads(
            self.path.read_text(encoding="utf-8")
        )

        return payload.get("drafts", [])

    def save(self, drafts: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "version": 1,
            "draft_count": len(drafts),
            "drafts": drafts,
        }

        self.path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def add(self, draft: dict[str, Any]) -> None:
        drafts = self.load()
        drafts.append(draft)
        self.save(drafts)

    def get(self, draft_id: str) -> dict[str, Any] | None:
        for draft in self.load():
            if draft.get("id") == draft_id:
                return draft

        return None

    def update(self, draft_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        drafts = self.load()

        for draft in drafts:
            if draft.get("id") == draft_id:
                draft.update(updates)
                self.save(drafts)
                return draft

        return None
