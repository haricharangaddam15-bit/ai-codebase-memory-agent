from __future__ import annotations

from typing import Any

from hindsight_client import Hindsight


class HindsightService:
    """
    Application wrapper around Hindsight.

    Hindsight is the project's long-term memory store.

    FastAPI uses the async Hindsight methods so we never block
    the application event loop.
    """

    def __init__(
        self,
        base_url: str,
        bank_id: str,
        api_key: str | None = None,
    ):
        self.base_url = base_url
        self.bank_id = bank_id

        self.client = Hindsight(
            base_url=base_url,
            api_key=api_key,
        )

    async def retain(
        self,
        content: str,
        *,
        context: str | None = None,
        document_id: str | None = None,
        metadata: dict[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> Any:
        return await self.client.aretain(
            bank_id=self.bank_id,
            content=content,
            context=context,
            document_id=document_id,
            metadata=metadata,
            tags=tags,
        )

    async def recall(
        self,
        query: str,
        *,
        budget: str = "mid",
        types: list[str] | None = None,
    ) -> Any:
        return await self.client.arecall(
            bank_id=self.bank_id,
            query=query,
            budget=budget,
            types=types,
        )

    async def reflect(
        self,
        query: str,
        *,
        context: str | None = None,
        budget: str = "low",
    ) -> Any:
        return await self.client.areflect(
            bank_id=self.bank_id,
            query=query,
            context=context,
            budget=budget,
        )

    async def close(self) -> None:
        """Close the underlying Hindsight HTTP client."""
        await self.client.aclose()

    async def create_bank(
        self,
        *,
        name: str | None = None,
        retain_mission: str | None = None,
        reflect_mission: str | None = None,
    ) -> Any:
        return await self.client.acreate_bank(
            bank_id=self.bank_id,
            name=name,
            retain_mission=retain_mission,
            reflect_mission=reflect_mission,
        )
