from backend.app.agents.pr_review_agent import PRReviewAgent


MEMORY = {
    "memory_type": "decision",
    "title": "Architecture: choose Redis for session cache",
    "summary": "PR #102 records an engineering decision.",
    "rationale": (
        "because session reads require low latency "
        "and temporary key expiration."
    ),
    "evidence": {
        "quote": (
            "We decided to use Redis because session reads "
            "require low latency and temporary key expiration."
        ),
        "source_url": "https://github.com/example/repo/pull/102",
        "source_type": "github",
        "source_id": "pr-102",
    },
    "alternatives": [],
    "decided_by": "developer",
    "module": "backend/services",
    "file_paths": [
        "backend/services/session_cache.py",
    ],
    "status": "active",
    "confidence": 0.8,
    "superseded_by": None,
}


agent = PRReviewAgent()


def test_conflicting_technology_change():
    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_cache.py
--- a/backend/services/session_cache.py
+++ b/backend/services/session_cache.py
@@ -1,2 +1,2 @@
-from redis import Redis
+from memcached import Client
"""

    comments = agent.review(diff, [MEMORY])

    assert len(comments) == 1
    assert comments[0]["memory_title"] == (
        "Architecture: choose Redis for session cache"
    )
    assert "low latency" in comments[0]["body"]
    assert comments[0]["evidence_quote"]


def test_unrelated_technology_does_not_trigger_review():
    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_cache.py
--- a/backend/services/session_cache.py
+++ b/backend/services/session_cache.py
@@ -1,2 +1,3 @@
 from redis import Redis
+import postgresql
"""

    comments = agent.review(diff, [MEMORY])

    assert comments == []


def test_unrelated_file_does_not_trigger_review():
    diff = """\
diff --git a/backend/api/users.py b/backend/api/users.py
--- a/backend/api/users.py
+++ b/backend/api/users.py
@@ -1,3 +1,4 @@
 def get_user():
+    return {"ok": True}
"""

    comments = agent.review(diff, [MEMORY])

    assert comments == []


def test_memory_without_evidence_is_ignored():
    memory = dict(MEMORY)
    memory["evidence"] = {
        "quote": "",
        "source_url": "",
    }

    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_cache.py
--- a/backend/services/session_cache.py
+++ b/backend/services/session_cache.py
@@ -1,2 +1,2 @@
-from redis import Redis
+from memcached import Client
"""

    comments = agent.review(diff, [memory])

    assert comments == []


def test_no_memory_means_no_review_comments():
    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_cache.py
--- a/backend/services/session_cache.py
+++ b/backend/services/session_cache.py
@@ -1,2 +1,2 @@
-from redis import Redis
+from memcached import Client
"""

    comments = agent.review(diff, [])

    assert comments == []


def test_memory_off_is_handled_by_api_layer():
    # Agent itself is intentionally memory-agnostic.
    # The API layer prevents review when memory is disabled.
    assert agent.review("", [MEMORY]) == []


def test_maximum_five_comments():
    memories = []

    for index in range(10):
        memory = dict(MEMORY)
        memory["title"] = (
            f"Architecture: choose Redis for session cache {index}"
        )
        memory["evidence"] = dict(MEMORY["evidence"])
        memory["evidence"]["source_id"] = f"pr-{index}"
        memories.append(memory)

    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_cache.py
--- a/backend/services/session_cache.py
+++ b/backend/services/session_cache.py
@@ -1,2 +1,2 @@
-from redis import Redis
+from memcached import Client
"""

    comments = agent.review(diff, memories)

    assert len(comments) <= 5


if __name__ == "__main__":
    test_conflicting_technology_change()
    test_unrelated_technology_does_not_trigger_review()
    test_unrelated_file_does_not_trigger_review()
    test_memory_without_evidence_is_ignored()
    test_no_memory_means_no_review_comments()
    test_memory_off_is_handled_by_api_layer()
    test_maximum_five_comments()

    print("All PR Review Agent Stage 2 tests passed.")
