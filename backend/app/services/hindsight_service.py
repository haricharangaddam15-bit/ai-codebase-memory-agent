from typing import Any

from hindsight_client import Hindsight


class HindsightService:
    """
    Thin application wrapper around Hindsight.

    Hindsight is the only long-term memory store.
    """

    def __init__(self, base_url: str, bank_id: str):
        self.base_url = base_url
        self.bank_id = bank_id
        self.client = Hindsight(base_url=base_url)

    def retain(
        self,
        content: str,
        *,
        context: str | None = None,
        document_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Any:
        return self.client.retain(
            bank_id=self.bank_id,
            content=content,
            context=context,
            document_id=document_id,
            metadata=metadata,
        )

    def recall(self, query: str, *, budget: str = "low") -> Any:
        return self.client.recall(
            bank_id=self.bank_id,
            query=query,
            budget=budget,
        )

    def reflect(self, query: str, *, context: str | None = None) -> Any:
        return self.client.reflect(
            bank_id=self.bank_id,
            query=query,
            context=context,
        )
