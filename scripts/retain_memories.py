from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from backend.app.services.hindsight_service import HindsightService
from backend.app.services.memory_serializer import serialize_memory
from backend.app.schemas.memory import DecisionMemory


ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")


async def main() -> None:
    hindsight_url = os.getenv(
        "HINDSIGHT_URL",
        "http://localhost:8888",
    )

    bank_id = os.getenv(
        "HINDSIGHT_BANK_ID",
        "codebase-memory",
    )

    input_path = (
        ROOT
        / "data"
        / "processed"
        / "ingestion.json"
    )

    if not input_path.exists():
        raise SystemExit(
            f"Missing ingestion file: {input_path}"
        )

    data = json.loads(
        input_path.read_text()
    )

    memories = [
        DecisionMemory.model_validate(item)
        for item in data.get("memories", [])
    ]

    print("===== HINDSIGHT INGESTION =====")
    print(f"URL: {hindsight_url}")
    print(f"Bank: {bank_id}")
    print(f"Memories: {len(memories)}")
    print()

    service = HindsightService(
        base_url=hindsight_url,
        bank_id=bank_id,
    )

    print("===== CREATE / UPDATE MEMORY BANK =====")

    await service.create_bank(
        name="AI Codebase Memory",
        retain_mission=(
            "Remember software engineering decisions, "
            "their rationale, alternatives, evidence, "
            "and project-specific conventions. "
            "Never invent undocumented rationale."
        ),
        reflect_mission=(
            "Answer questions about software project history "
            "using grounded memories and cite the source evidence."
        ),
    )

    print("Memory bank ready.")
    print()

    for index, memory in enumerate(memories, start=1):
        content = serialize_memory(memory)

        print(
            f"Retaining memory {index}/{len(memories)}: "
            f"{memory.title}"
        )

        result = await service.retain(
            content,
            context=(
                f"GitHub PR #{memory.evidence.source_id} "
                f"in the codebase memory project"
            ),
            document_id=(
                f"github-pr-{memory.evidence.source_id}"
            ),
            metadata={
                "memory_type": memory.memory_type.value,
                "status": memory.status.value,
                "module": memory.module,
                "source_url": memory.evidence.source_url,
                "source_id": memory.evidence.source_id,
            },
            tags=[
                "github",
                "decision",
                memory.status.value,
            ],
        )

        print(
            f"  success={getattr(result, 'success', None)}"
        )
        print(
            f"  items_count={getattr(result, 'items_count', None)}"
        )

    print()
    print("===== COMPLETE =====")


if __name__ == "__main__":
    asyncio.run(main())
