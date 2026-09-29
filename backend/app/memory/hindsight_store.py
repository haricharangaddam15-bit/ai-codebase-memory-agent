from __future__ import annotations

from typing import Any

from backend.app.memory.local_store import (
    LocalMemoryStore,
    normalize_source_url,
)
from backend.app.services.hindsight_service import HindsightService


class HindsightMemoryStore:
    """
    Hindsight-backed semantic retrieval over canonical DecisionMemory records.

    Hindsight retrieves semantic candidates.
    The canonical LocalMemoryStore verifies that the candidate is
    actually relevant to the documented decision query.

    The canonical record remains authoritative for:
    - rationale
    - evidence
    - citation
    - status
    """

    def __init__(
        self,
        memory_path: str,
        hindsight_service: HindsightService,
    ):
        self.canonical_store = LocalMemoryStore(memory_path)
        self.hindsight_service = hindsight_service

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query = query.strip()

        if not query:
            return []

        response = await self.hindsight_service.recall(
            query,
            budget="low",
        )

        # First establish which canonical memories are actually
        # relevant to the question using the tested local relevance
        # guard. Hindsight can then select/rank among those candidates.
        canonical_candidates = self.canonical_store.search(
            query,
            limit=limit,
        )

        if not canonical_candidates:
            return []

        canonical_by_source_id: dict[
            str,
            dict[str, Any],
        ] = {}

        for memory in canonical_candidates:
            evidence = memory.get("evidence", {})

            source_id = str(
                evidence.get("source_id", "")
            ).strip()

            source_type = str(
                evidence.get("source_type", "")
            ).strip()

            source_url = normalize_source_url(
                str(evidence.get("source_url", ""))
            )

            if not source_id:
                continue

            if source_type not in {"github_pr", "github"}:
                continue

            canonical = dict(memory)

            canonical_evidence = dict(
                canonical.get("evidence", {})
            )

            canonical_evidence["source_url"] = source_url
            canonical["evidence"] = canonical_evidence

            canonical_by_source_id[source_id] = canonical

        if not canonical_by_source_id:
            return []

        results: list[tuple[float, dict[str, Any]]] = []
        seen_source_ids: set[str] = set()

        for item in response.results:
            metadata = getattr(item, "metadata", None) or {}

            source_id = str(
                metadata.get("source_id", "")
            ).strip()

            document_id = str(
                getattr(item, "document_id", "") or ""
            ).strip()

            if not source_id:
                if document_id.startswith("github-pr-"):
                    source_id = document_id.removeprefix(
                        "github-pr-"
                    ).strip()

            if not source_id:
                continue

            if source_id in seen_source_ids:
                continue

            memory = canonical_by_source_id.get(
                source_id
            )

            if memory is None:
                continue

            status = str(
                memory.get("status", "active")
            ).strip()

            if status != "active":
                continue

            evidence = memory.get("evidence", {})

            if not str(
                evidence.get("quote", "")
            ).strip():
                continue

            score_object = getattr(item, "scores", None)

            score = float(
                getattr(
                    score_object,
                    "final",
                    0.0,
                )
                or 0.0
            )

            results.append(
                (
                    score,
                    memory,
                )
            )

            seen_source_ids.add(source_id)

        results.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            memory
            for _, memory in results[:limit]
        ]
