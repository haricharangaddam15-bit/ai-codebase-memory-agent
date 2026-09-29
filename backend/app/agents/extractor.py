from __future__ import annotations

import json
import re
from typing import Any

from backend.app.schemas.ingestion import PRSource
from backend.app.schemas.memory import (
    DecisionMemory,
    Evidence,
    MemoryStatus,
    MemoryType,
)


class DecisionExtractor:
    """
    Base interface for decision extraction.

    Production extraction will use an LLM with structured output.
    """

    def extract(self, pr: PRSource) -> list[DecisionMemory]:
        raise NotImplementedError


class RuleBasedDecisionExtractor(DecisionExtractor):
    """
    Deterministic extraction layer used before the LLM.

    Safety rules:
    - Evidence must come directly from source text.
    - No evidence means no memory.
    - Missing rationale becomes "not documented".
    - Source URLs are normalized.
    """

    DECISION_SIGNALS = (
        "we decided",
        "we chose",
        "selected",
        "accepted",
        "use ",
        "using ",
    )

    RATIONALE_SIGNALS = (
        "because",
        "because of",
        "due to",
        "reason",
    )

    ALTERNATIVE_SIGNALS = (
        "we considered",
        "alternative",
        "instead of",
        "rejected",
    )

    def extract(self, pr: PRSource) -> list[DecisionMemory]:
        text = self._build_source_text(pr)

        if not self._contains_decision_signal(text):
            return []

        evidence_quote = self._find_evidence(text)

        if not evidence_quote:
            return []

        rationale = self._extract_rationale(text)
        alternatives = self._extract_alternatives(text)

        memory = DecisionMemory(
            memory_type=MemoryType.decision,
            title=pr.title.strip(),
            summary=pr.title.strip(),
            rationale=rationale,
            evidence=Evidence(
                quote=evidence_quote,
                source_url=self._normalize_url(pr.url),
                source_type="github_pr",
                source_id=str(pr.number),
                author=pr.author,
            ),
            alternatives=alternatives,
            decided_by=pr.author,
            module=self._infer_module(pr),
            file_paths=pr.changed_files,
            status=MemoryStatus.active,
            confidence=0.75 if rationale != "not documented" else 0.55,
        )

        memory.validate_rationale()

        return [memory]

    def _build_source_text(self, pr: PRSource) -> str:
        sections = [
            f"PR TITLE:\n{pr.title}",
            f"PR BODY:\n{pr.body}",
        ]

        if pr.comments:
            sections.append(
                "PR COMMENTS:\n" + "\n".join(pr.comments)
            )

        if pr.changed_files:
            sections.append(
                "CHANGED FILES:\n" + "\n".join(pr.changed_files)
            )

        return "\n\n".join(sections)

    def _contains_decision_signal(self, text: str) -> bool:
        lowered = text.lower()

        return any(
            signal in lowered
            for signal in self.DECISION_SIGNALS
        )

    def _clean_sentence(self, sentence: str) -> str:
        sentence = re.sub(
            r"^#+\s*[^:]+[:?]?\s*",
            "",
            sentence.strip(),
        )

        sentence = re.sub(
            r"^[-*]\s*",
            "",
            sentence,
        )

        return sentence.strip()

    def _find_evidence(self, text: str) -> str | None:
        """
        Find the strongest verbatim rationale sentence.

        Evidence is never generated. It must already exist in the source.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        candidates: list[str] = []

        for sentence in sentences:
            cleaned = self._clean_sentence(sentence)

            if not cleaned:
                continue

            lowered = cleaned.lower()

            if "because" in lowered:
                candidates.append(cleaned)
                continue

            if "due to" in lowered:
                candidates.append(cleaned)
                continue

            if "was selected" in lowered:
                candidates.append(cleaned)
                continue

            if "was chosen" in lowered:
                candidates.append(cleaned)
                continue

        if not candidates:
            return None

        return max(
            candidates,
            key=len,
        )[:1000]

    def _extract_rationale(self, text: str) -> str:
        """
        Extract only rationale sentences.

        Do not allow alternative/rejection sections to leak into rationale.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        rationale_parts: list[str] = []

        for sentence in sentences:
            cleaned = self._clean_sentence(sentence)

            if not cleaned:
                continue

            lowered = cleaned.lower()

            if any(
                signal in lowered
                for signal in self.RATIONALE_SIGNALS
            ):
                rationale_parts.append(cleaned)

        if not rationale_parts:
            return "not documented"

        return " ".join(rationale_parts)[:2000]

    def _extract_alternatives(self, text: str) -> list[str]:
        """
        Extract explicit alternative/rejection statements separately.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        alternatives: list[str] = []

        for sentence in sentences:
            cleaned = self._clean_sentence(sentence)

            if not cleaned:
                continue

            lowered = cleaned.lower()

            if "rejected" in lowered:
                alternatives.append(cleaned)
                continue

            if "instead of" in lowered:
                alternatives.append(cleaned)
                continue

            if "we considered" in lowered:
                alternatives.append(cleaned)
                continue

        return alternatives[:10]

    def _infer_module(self, pr: PRSource) -> str:
        if not pr.changed_files:
            return ""

        first = pr.changed_files[0]
        parts = first.split("/")

        if len(parts) >= 2:
            return "/".join(parts[:2])

        return first

    def _normalize_url(self, url: str) -> str:
        """
        Normalize accidentally supplied Markdown links:

        [https://example.com](https://example.com)

        ->

        https://example.com
        """

        match = re.fullmatch(
            r"\[(https?://[^\]]+)\]\((https?://[^)]+)\)",
            url.strip(),
        )

        if match:
            return match.group(2)

        return url.strip()

    def _build_source_text_for_debug(self, pr: PRSource) -> str:
        return self._build_source_text(pr)


def memory_to_json(memory: DecisionMemory) -> dict[str, Any]:
    return memory.model_dump(mode="json")


def memory_to_pretty_json(memory: DecisionMemory) -> str:
    return json.dumps(
        memory_to_json(memory),
        indent=2,
        ensure_ascii=False,
    )
