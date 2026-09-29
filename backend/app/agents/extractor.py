from backend.app.schemas.ingestion import PRSource
from backend.app.schemas.memory import DecisionMemory


class DecisionExtractor:
    """
    Extraction interface.

    The production implementation will call the configured LLM with
    structured JSON output. This class deliberately does not invent
    rationale when the source does not contain one.
    """

    def extract(self, pr: PRSource) -> list[DecisionMemory]:
        raise NotImplementedError(
            "LLM extraction will be implemented in the next build step."
        )
