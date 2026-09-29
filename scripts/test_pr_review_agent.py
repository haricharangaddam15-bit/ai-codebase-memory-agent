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


def test_inactive_memory_is_ignored():
    memory = dict(MEMORY)
    memory["status"] = "superseded"
    memory["superseded_by"] = "pr-200"

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


def test_superseded_memory_is_ignored_even_if_status_is_active():
    memory = dict(MEMORY)
    memory["superseded_by"] = "pr-200"

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




def test_deleted_file_conflict_is_detected():
    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_cache.py
deleted file mode 100644
--- a/backend/services/session_cache.py
+++ /dev/null
@@ -1,2 +0,0 @@
-from redis import Redis
-class SessionCache:
-    pass
"""

    comments = agent.review(diff, [MEMORY])

    assert len(comments) == 1
    assert comments[0]["memory_title"] == (
        "Architecture: choose Redis for session cache"
    )


def test_renamed_file_with_conflict_is_detected():
    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_store.py
similarity index 80%
rename from backend/services/session_cache.py
rename to backend/services/session_store.py
--- a/backend/services/session_cache.py
+++ b/backend/services/session_store.py
@@ -1,2 +1,2 @@
-from redis import Redis
+from memcached import Client
"""

    comments = agent.review(diff, [MEMORY])

    assert len(comments) == 1


def test_documentation_only_technology_mention_does_not_trigger():
    diff = """\
diff --git a/docs/architecture/backend-framework.md b/docs/architecture/backend-framework.md
--- a/docs/architecture/backend-framework.md
+++ b/docs/architecture/backend-framework.md
@@ -1,2 +1,3 @@
 The backend uses Redis for session caching.
+Redis documentation has been updated.
+This does not change the implementation.
"""

    comments = agent.review(diff, [MEMORY])

    assert comments == []


def test_same_technology_change_does_not_trigger():
    diff = """\
diff --git a/backend/services/session_cache.py b/backend/services/session_cache.py
--- a/backend/services/session_cache.py
+++ b/backend/services/session_cache.py
@@ -1,2 +1,2 @@
-from redis import Redis
+from redis import Redis as SessionRedis
"""

    comments = agent.review(diff, [MEMORY])

    assert comments == []


def test_unrelated_file_with_same_filename_does_not_trigger():
    diff = """\
diff --git a/tests/session_cache.py b/tests/session_cache.py
--- a/tests/session_cache.py
+++ b/tests/session_cache.py
@@ -1,2 +1,2 @@
-from redis import Redis
+from memcached import Client
"""

    comments = agent.review(diff, [MEMORY])

    assert comments == []


if __name__ == "__main__":
    test_conflicting_technology_change()
    test_unrelated_technology_does_not_trigger_review()
    test_unrelated_file_does_not_trigger_review()
    test_memory_without_evidence_is_ignored()
    test_no_memory_means_no_review_comments()
    test_memory_off_is_handled_by_api_layer()
    test_maximum_five_comments()
    test_deleted_file_conflict_is_detected()
    test_renamed_file_with_conflict_is_detected()
    test_documentation_only_technology_mention_does_not_trigger()
    test_same_technology_change_does_not_trigger()
    test_unrelated_file_with_same_filename_does_not_trigger()
    test_inactive_memory_is_ignored()
    test_superseded_memory_is_ignored_even_if_status_is_active()
    print("All PR Review Agent Stage 4 tests passed.")
