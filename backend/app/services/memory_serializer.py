from __future__ import annotations

import json

from backend.app.schemas.memory import DecisionMemory


def serialize_memory(memory: DecisionMemory) -> str:
    """
    Convert a typed DecisionMemory into a rich textual memory.

    The source evidence is deliberately included in the retained
    content so recalled memories can explain where the decision came from.
    """

    payload = {
        "memory_type": memory.memory_type.value,
        "title": memory.title,
        "summary": memory.summary,
        "rationale": memory.rationale,
        "alternatives": memory.alternatives,
        "decided_by": memory.decided_by,
        "module": memory.module,
        "file_paths": memory.file_paths,
        "status": memory.status.value,
        "confidence": memory.confidence,
        "evidence": {
            "quote": memory.evidence.quote,
            "source_url": memory.evidence.source_url,
            "source_type": memory.evidence.source_type,
            "source_id": memory.evidence.source_id,
            "author": memory.evidence.author,
        },
        "superseded_by": memory.superseded_by,
    }

    return json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )
