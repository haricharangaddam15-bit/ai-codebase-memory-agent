from unittest.mock import MagicMock, patch

from backend.app.ingestion.github_source import GitHubSource


def build_source():
    source = object.__new__(GitHubSource)
    source.github = MagicMock()
    source.repo = MagicMock()
    source.token = "test-token"
    source.repository = "example/repo"
    return source


def test_fetch_pull_request():
    source = build_source()

    pr = MagicMock()
    pr.number = 102
    pr.title = "Architecture: choose Redis for session cache"
    pr.body = (
        "We decided to use Redis because session reads "
        "require low latency and temporary key expiration."
    )
    pr.html_url = (
        "https://github.com/example/repo/pull/102"
    )
    pr.user.login = "developer"
    pr.state = "open"
    pr.merged = False
    pr.created_at.isoformat.return_value = (
        "2026-09-29T00:00:00+00:00"
    )
    pr.updated_at.isoformat.return_value = (
        "2026-09-29T00:00:00+00:00"
    )

    issue_comment = MagicMock()
    issue_comment.body = "Looks good."

    review_comment = MagicMock()
    review_comment.body = "Please document the rationale."

    changed_file = MagicMock()
    changed_file.filename = (
        "backend/services/session_cache.py"
    )
    changed_file.patch = (
        "@@ -1,2 +1,2 @@\n"
        "-from redis import Redis\n"
        "+from memcached import Client\n"
    )

    pr.get_issue_comments.return_value = [
        issue_comment
    ]
    pr.get_review_comments.return_value = [
        review_comment
    ]
    pr.get_files.return_value = [
        changed_file
    ]

    source.repo.get_pull.return_value = pr

    result = source.fetch_pull_request(102)

    assert result.number == 102
    assert result.title == (
        "Architecture: choose Redis for session cache"
    )
    assert result.changed_files == [
        "backend/services/session_cache.py"
    ]
    assert result.comments == [
        "Looks good.",
        "Please document the rationale.",
    ]


def test_fetch_pull_request_diff():
    source = build_source()

    response = MagicMock()
    response.text = (
        "diff --git a/backend/services/session_cache.py "
        "b/backend/services/session_cache.py\n"
        "--- a/backend/services/session_cache.py\n"
        "+++ b/backend/services/session_cache.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-from redis import Redis\n"
        "+from memcached import Client\n"
        "diff --git a/backend/api/users.py "
        "b/backend/api/users.py\n"
        "--- a/backend/api/users.py\n"
        "+++ b/backend/api/users.py\n"
        "@@ -1,1 +1,2 @@\n"
        " def get_user():\n"
        "+    return {'ok': True}\n"
    )

    with patch(
        "backend.app.ingestion.github_source.httpx.get",
        return_value=response,
    ) as mock_get:
        diff = source.fetch_pull_request_diff(102)

    expected_url = (
        "https"
        + "://"
        + "api.github.com/repos/example/repo/pulls/102"
    )

    mock_get.assert_called_once_with(
        expected_url,
        headers={
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": "Bearer test-token",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30.0,
    )

    assert (
        "diff --git a/backend/services/session_cache.py "
        "b/backend/services/session_cache.py"
    ) in diff
    assert "-from redis import Redis" in diff
    assert "+from memcached import Client" in diff
    assert (
        "diff --git a/backend/api/users.py "
        "b/backend/api/users.py"
    ) in diff

def test_rename_metadata_is_preserved():
    source = build_source()

    response = MagicMock()
    response.text = (
        "diff --git a/docs/architecture/backend-framework.md "
        "b/docs/architecture/backend-framework-flask.md\n"
        "similarity index 86%\n"
        "rename from docs/architecture/backend-framework.md\n"
        "rename to docs/architecture/backend-framework-flask.md\n"
        "--- a/docs/architecture/backend-framework.md\n"
        "+++ b/docs/architecture/backend-framework-flask.md\n"
        "@@ -2,7 +2,7 @@\n"
        "-The AI Codebase Memory Agent backend uses FastAPI.\n"
        "+The AI Codebase Memory Agent backend uses Flask.\n"
    )

    with patch(
        "backend.app.ingestion.github_source.httpx.get",
        return_value=response,
    ):
        diff = source.fetch_pull_request_diff(102)

    assert (
        "rename from docs/architecture/backend-framework.md"
        in diff
    )
    assert (
        "rename to docs/architecture/backend-framework-flask.md"
        in diff
    )
    assert (
        "--- a/docs/architecture/backend-framework.md"
        in diff
    )
    assert (
        "+++ b/docs/architecture/backend-framework-flask.md"
        in diff
    )


def test_http_error_is_propagated():
    source = build_source()

    response = MagicMock()
    response.raise_for_status.side_effect = RuntimeError(
        "GitHub error"
    )

    with patch(
        "backend.app.ingestion.github_source.httpx.get",
        return_value=response,
    ):
        try:
            source.fetch_pull_request_diff(102)
        except RuntimeError as exc:
            assert str(exc) == "GitHub error"
        else:
            raise AssertionError("Expected GitHub error")


def test_github_diff_error_is_propagated():
    source = build_source()

    response = MagicMock()
    response.raise_for_status.side_effect = RuntimeError(
        "GitHub diff request failed"
    )

    with patch(
        "backend.app.ingestion.github_source.httpx.get",
        return_value=response,
    ):
        try:
            source.fetch_pull_request_diff(102)
        except RuntimeError as exc:
            assert str(exc) == "GitHub diff request failed"
        else:
            raise AssertionError(
                "Expected GitHub diff request failure"
            )


if __name__ == "__main__":
    test_fetch_pull_request()
    test_fetch_pull_request_diff()
    test_rename_metadata_is_preserved()
    test_http_error_is_propagated()
    test_github_diff_error_is_propagated()
    print("All GitHub review source tests passed.")
