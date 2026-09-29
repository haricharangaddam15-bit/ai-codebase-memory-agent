from __future__ import annotations

import tempfile
from pathlib import Path

from backend.app.agents.qa_agent import QAAgent
from backend.app.api import routes
from backend.app.memory.capture_store import CaptureStore
from backend.app.memory.local_store import LocalMemoryStore
from backend.app.schemas.capture import (
    CaptureCreateRequest,
    CaptureReviewRequest,
)
from backend.app.schemas.ingestion import PRSource


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        original_memory_store = routes.memory_store
        original_qa_agent = routes.qa_agent
        original_capture_store = routes.capture_store

        try:
            memory_store = LocalMemoryStore(
                str(temp_path / "memories.json")
            )
            capture_store = CaptureStore(
                str(temp_path / "drafts.json")
            )

            routes.memory_store = memory_store
            routes.qa_agent = QAAgent(memory_store)
            routes.capture_store = capture_store

            pr = PRSource(
                number=501,
                title="Architecture: choose Redis",
                body=(
                    "We decided to use Redis because "
                    "it provides low-latency caching for session data."
                ),
                url=(
                    "https://github.com/example/"
                    "ai-codebase-memory-agent/pull/501"
                ),
                author="integration-test",
                state="closed",
                merged=True,
                changed_files=["backend/cache/session_store.py"],
            )

            # 1. Create an evidence-backed capture draft.
            draft = routes.create_capture_draft(
                CaptureCreateRequest(pr=pr)
            )

            assert draft["status"] == "pending"
            draft_id = draft["id"]

            print("PASS: capture draft created.")
            print("Draft ID:", draft_id)

            # 2. Confirm it is pending before human approval.
            stored_draft = routes.list_capture_drafts()
            assert len(stored_draft["drafts"]) == 1
            assert stored_draft["drafts"][0]["status"] == "pending"

            print("PASS: draft is pending human review.")

            # 3. Approve the draft.
            approved = routes.approve_capture_draft(
                draft_id,
                CaptureReviewRequest(reviewer="integration-test"),
            )

            assert approved["status"] == "approved"
            assert approved["reviewed_by"] == "integration-test"

            print("PASS: draft approved.")

            # 4. Verify the approved memory was persisted.
            memories = memory_store.load()

            assert len(memories) == 1
            assert memories[0]["title"] == (
                "Architecture: choose Redis"
            )
            assert memories[0]["evidence"]["quote"]
            assert memories[0]["evidence"]["source_id"] == "pr-501"

            print("PASS: approved memory persisted.")

            # 5. Verify Q&A can retrieve the newly captured memory.
            qa_result = routes.qa_agent.ask(
                "Why did we choose Redis?",
                memory_enabled=True,
            )

            assert qa_result.documented is True
            assert len(qa_result.memories) >= 1
            assert qa_result.memories[0]["title"] == (
                "Architecture: choose Redis"
            )
            assert len(qa_result.citations) >= 1

            print("PASS: Q&A retrieved the newly captured memory.")
            print("Answer:", qa_result.answer)
            print("Citation:", qa_result.citations[0])

            # 6. Verify memory-disabled Q&A does not use the memory.
            disabled_result = routes.qa_agent.ask(
                "Why did we choose Redis?",
                memory_enabled=False,
            )

            assert disabled_result.documented is False
            assert disabled_result.memories == []
            assert disabled_result.citations == []

            print("PASS: memory-disabled Q&A used no memory.")

            # 7. Verify the draft itself is now approved.
            final_draft = routes.capture_store.get(draft_id)

            assert final_draft is not None
            assert final_draft["status"] == "approved"

            print("PASS: final capture state is approved.")

        finally:
            routes.memory_store = original_memory_store
            routes.qa_agent = original_qa_agent
            routes.capture_store = original_capture_store

    print("\nAll Capture Integration tests passed.")


if __name__ == "__main__":
    main()
