from __future__ import annotations

import json
from pathlib import Path

from backend.app.memory.local_store import LocalMemoryStore


INPUT = Path("data/processed/ingestion.json")
OUTPUT = Path("data/memory/memories.json")


def main() -> None:
    if not INPUT.exists():
        raise SystemExit(f"Missing input: {INPUT}")

    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    memories = payload.get("memories", [])

    if not memories:
        raise SystemExit("No memories found in ingestion output.")

    # Safety rule:
    # only persist memories that contain evidence.
    valid_memories = []

    for memory in memories:
        evidence = memory.get("evidence") or {}
        quote = str(evidence.get("quote", "")).strip()

        if not quote:
            print(
                f"SKIP: {memory.get('title', '<untitled>')} "
                "(no evidence quote)"
            )
            continue

        valid_memories.append(memory)

    store = LocalMemoryStore(str(OUTPUT))
    store.save(valid_memories)

    print("===== LOCAL MEMORY BUILD =====")
    print(f"Input memories: {len(memories)}")
    print(f"Stored memories: {len(valid_memories)}")
    print(f"Memory file: {OUTPUT}")


if __name__ == "__main__":
    main()
