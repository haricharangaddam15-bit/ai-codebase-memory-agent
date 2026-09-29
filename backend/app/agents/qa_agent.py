from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.memory.hindsight_store import HindsightMemoryStore


@dataclass
class QAAnswer:
    question: str
    answer: str
    documented: bool
    memories: list[dict[str, Any]]
    citations: list[dict[str, str]]


class QAAgent:
    """
    Evidence-grounded Q&A over Hindsight-backed codebase memory.

    Rules:
    - Use only retrieved memories.
    - Never invent undocumented rationale.
    - Every documented answer must contain evidence and source information.
    - Return NOT DOCUMENTED when no relevant memory exists.
    """

    def __init__(self, store: HindsightMemoryStore):
        self.store = store

    async def ask(
        self,
        question: str,
        memory_enabled: bool = True,
    ) -> QAAnswer:
        question = question.strip()

        if not question:
            return QAAnswer(
                question=question,
                answer="NOT DOCUMENTED",
                documented=False,
                memories=[],
                citations=[],
            )

        if not memory_enabled:
            return QAAnswer(
                question=question,
                answer=(
                    "Memory is disabled for this request. "
                    "No codebase memory was used."
                ),
                documented=False,
                memories=[],
                citations=[],
            )

        memories = await self.store.search(question)

        if not memories:
            return QAAnswer(
                question=question,
                answer="NOT DOCUMENTED",
                documented=False,
                memories=[],
                citations=[],
            )

        grounded_memories = []

        for memory in memories:
            evidence = memory.get("evidence", {})
            quote = str(evidence.get("quote", "")).strip()

            if not quote:
                continue

            grounded_memories.append(memory)

        if not grounded_memories:
            return QAAnswer(
                question=question,
                answer="NOT DOCUMENTED",
                documented=False,
                memories=[],
                citations=[],
            )

        primary = grounded_memories[0]

        title = str(
            primary.get(
                "title",
                "Documented decision",
            )
        )

        rationale = str(
            primary.get("rationale", "")
        ).strip()

        evidence = primary.get("evidence", {})

        quote = str(
            evidence.get("quote", "")
        ).strip()

        source_url = str(
            evidence.get("source_url", "")
        ).strip()

        answer = (
            f"{title}\n\n"
            f"Rationale:\n{rationale}\n\n"
            f"Evidence:\n{quote}"
        )

        citations = []

        if source_url:
            citations.append(
                {
                    "source_url": source_url,
                    "source_type": str(
                        evidence.get(
                            "source_type",
                            "unknown",
                        )
                    ),
                    "source_id": str(
                        evidence.get(
                            "source_id",
                            "",
                        )
                    ),
                }
            )

        return QAAnswer(
            question=question,
            answer=answer,
            documented=True,
            memories=grounded_memories,
            citations=citations,
        )
