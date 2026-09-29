from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.schemas.ingestion import PRSource
from backend.app.memory.local_store import normalize_source_url
from backend.app.schemas.memory import (
    DecisionMemory,
    Evidence,
    MemoryStatus,
    MemoryType,
)


DECISION_SIGNALS = (
    "we decided",
    "we chose",
    "we choose",
    "selected",
    "instead of",
    "we will use",
    "we use",
    "because",
    "trade-off",
    "tradeoff",
    "architecture",
    "decision",
    "rejected",
)

RATIONALE_SIGNALS = (
    "because",
    "due to",
    "so that",
    "in order to",
    "for this reason",
    "the reason",
    "trade-off",
    "tradeoff",
)


class CaptureAgent:
    """
    Creates evidence-backed decision drafts from merged PRs.

    The agent never invents undocumented rationale.
    """

    def draft(self, pr: PRSource) -> dict | None:
        if not pr.merged:
            return None

        source_text = self._build_source_text(pr)

        evidence_quote = self._find_evidence(source_text)

        if not evidence_quote:
            return None

        rationale = self._extract_rationale(evidence_quote)

        if not rationale:
            return None

        memory = DecisionMemory(
            memory_type=MemoryType.decision,
            title=self._build_title(pr),
            summary=self._build_summary(pr, rationale),
            rationale=rationale,
            evidence=Evidence(
                quote=evidence_quote,
                source_url=normalize_source_url(pr.url),
                source_type="github",
                source_id=f"pr-{pr.number}",
                author=pr.author,
                date=self._parse_date(
                    pr.updated_at or pr.created_at
                ),
            ),
            alternatives=self._extract_alternatives(source_text),
            decided_by=pr.author,
            module=self._infer_module(pr.changed_files),
            file_paths=pr.changed_files,
            status=MemoryStatus.active,
            confidence=0.80,
        )

        memory.validate_rationale()

        return {
            "id": str(uuid4()),
            "status": "pending",
            "memory": memory.model_dump(mode="json"),
            "source_pr": pr.model_dump(mode="json"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _build_source_text(pr: PRSource) -> str:
        parts: list[str] = []

        if pr.title.strip():
            parts.append(pr.title.strip())

        if pr.body.strip():
            parts.append(pr.body.strip())

        for comment in pr.comments:
            if comment.strip():
                parts.append(comment.strip())

        return "\n\n".join(parts)

    @staticmethod
    def _find_evidence(text: str) -> str | None:
        """
        Find a complete sentence containing both a decision
        signal and a rationale signal.

        This prevents us from creating a draft from a bare
        statement such as "We decided to use MongoDB."
        """

        sentences = re.split(
            r"(?<=[.!?])\s+|\n+",
            text,
        )

        for sentence in sentences:
            cleaned = " ".join(sentence.split())

            if not cleaned:
                continue

            lowered = cleaned.lower()

            has_decision = any(
                signal in lowered
                for signal in DECISION_SIGNALS
            )

            has_rationale = any(
                signal in lowered
                for signal in RATIONALE_SIGNALS
            )

            if has_decision and has_rationale:
                return cleaned[:1000]

        return None

    @staticmethod
    def _extract_rationale(evidence: str) -> str | None:
        lowered = evidence.lower()

        for signal in RATIONALE_SIGNALS:
            position = lowered.find(signal)

            if position < 0:
                continue

            rationale = evidence[position:].strip()

            # Require actual explanatory content after
            # the rationale signal.
            remainder = rationale[len(signal):].strip()

            if len(remainder) >= 3:
                return rationale

        return None

    @staticmethod
    def _build_title(pr: PRSource) -> str:
        return (
            pr.title.strip()
            or f"Decision from PR #{pr.number}"
        )

    @staticmethod
    def _build_summary(
        pr: PRSource,
        rationale: str,
    ) -> str:
        return (
            f"PR #{pr.number} records an engineering decision. "
            f"Documented rationale: {rationale}"
        )

    @staticmethod
    def _extract_alternatives(
        text: str,
    ) -> list[str]:
        alternatives: list[str] = []

        for sentence in re.split(
            r"(?<=[.!?])\s+|\n+",
            text,
        ):
            cleaned = " ".join(sentence.split())
            lowered = cleaned.lower()

            if (
                "instead of" in lowered
                or "rejected" in lowered
            ):
                alternatives.append(cleaned[:500])

        return alternatives[:5]

    @staticmethod
    def _infer_module(
        changed_files: list[str],
    ) -> str:
        if not changed_files:
            return ""

        first = changed_files[0]
        parts = first.split("/")

        if len(parts) <= 1:
            return ""

        return "/".join(parts[:-1])

    @staticmethod
    def _parse_date(
        value: str,
    ) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None
