from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.agents.extractor import DecisionExtractor
from backend.app.ingestion.signal_filter import filter_prs
from backend.app.schemas.ingestion import PRSource
from backend.app.schemas.memory import DecisionMemory


@dataclass
class PipelineResult:
    input_count: int
    selected_count: int
    skipped_count: int
    memory_count: int
    memories: list[DecisionMemory] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class IngestionPipeline:
    def __init__(self, extractor: DecisionExtractor):
        self.extractor = extractor

    def process(self, prs: list[PRSource]) -> PipelineResult:
        selected, skipped = filter_prs(prs)

        memories: list[DecisionMemory] = []
        errors: list[str] = []

        for pr in selected:
            try:
                extracted = self.extractor.extract(pr)
                memories.extend(extracted)
            except Exception as exc:
                errors.append(
                    f"PR #{pr.number}: {type(exc).__name__}: {exc}"
                )

        return PipelineResult(
            input_count=len(prs),
            selected_count=len(selected),
            skipped_count=len(skipped),
            memory_count=len(memories),
            memories=memories,
            errors=errors,
        )
