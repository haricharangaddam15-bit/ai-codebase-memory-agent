from backend.app.agents.capture_agent import CaptureAgent
from backend.app.schemas.ingestion import PRSource


agent = CaptureAgent()


merged_pr = PRSource(
    number=2,
    title="Architecture: choose PostgreSQL",
    body=(
        "We decided to use PostgreSQL because "
        "we need transactional consistency and typed relational data."
    ),
    url="https://github.com/example/repo/pull/2",
    author="developer",
    state="closed",
    merged=True,
    changed_files=["backend/db/database.py"],
)

draft = agent.draft(merged_pr)

assert draft is not None
assert draft["status"] == "pending"

memory = draft["memory"]

assert memory["memory_type"] == "decision"
assert memory["evidence"]["quote"]
assert "because" in memory["rationale"].lower()

print("PASS: merged PR produced an evidence-backed capture draft.")
print("Draft title:", memory["title"])
print("Rationale:", memory["rationale"])
print("Evidence:", memory["evidence"]["quote"])


unmerged_pr = PRSource(
    number=3,
    title="Architecture: choose Redis",
    body=(
        "We decided to use Redis because it is appropriate "
        "for this caching requirement."
    ),
    url="https://github.com/example/repo/pull/3",
    author="developer",
    state="open",
    merged=False,
)

assert agent.draft(unmerged_pr) is None

print("PASS: unmerged PR was not captured.")


no_rationale_pr = PRSource(
    number=4,
    title="Architecture: choose MongoDB",
    body="We decided to use MongoDB.",
    url="https://github.com/example/repo/pull/4",
    author="developer",
    state="closed",
    merged=True,
)

assert agent.draft(no_rationale_pr) is None

print("PASS: decision without documented rationale was not captured.")

print("\nAll Capture Agent tests passed.")
