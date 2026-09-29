from __future__ import annotations

import json
from pathlib import Path

from backend.app.memory.local_store import (
    LocalMemoryStore,
    normalize_source_url,
)


ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "processed" / "ingestion.json"
OUTPUT = ROOT / "data" / "memory" / "memories.json"


def main():
    payload = json.loads(
        INPUT.read_text(encoding="utf-8")
    )

    memories = payload.get("memories", [])

    valid_memories = []

    for memory in memories:
        evidence = memory.get("evidence", {})
        quote = str(evidence.get("quote", "")).strip()

        if not quote:
            print(
                f"SKIP: {memory.get('title', '<untitled>')} "
                "(no evidence quote)"
            )
            continue

        normalized_memory = dict(memory)

        normalized_evidence = dict(evidence)

        if normalized_evidence.get("source_url"):
            normalized_evidence["source_url"] = normalize_source_url(
                normalized_evidence["source_url"]
            )

        normalized_memory["evidence"] = normalized_evidence

        valid_memories.append(normalized_memory)

    store = LocalMemoryStore(str(OUTPUT))
    store.save(valid_memories)

    print("===== LOCAL MEMORY BUILD =====")
    print(f"Input memories: {len(memories)}")
    print(f"Stored memories: {len(valid_memories)}")
    print(f"Memory file: {OUTPUT}")


if __name__ == "__main__":
    main()
