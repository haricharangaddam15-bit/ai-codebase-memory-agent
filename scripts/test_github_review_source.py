from unittest.mock import MagicMock

from backend.app.ingestion.github_source import GitHubSource


def build_source():
    source = object.__new__(GitHubSource)

    source.github = MagicMock()
    source.repo = MagicMock()

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

    pr = MagicMock()

    changed_file = MagicMock()
    changed_file.filename = (
        "backend/services/session_cache.py"
    )
    changed_file.patch = (
        "@@ -1,2 +1,2 @@\n"
        "-from redis import Redis\n"
        "+from memcached import Client\n"
    )

    second_file = MagicMock()
    second_file.filename = "backend/api/users.py"
    second_file.patch = (
        "@@ -1,1 +1,2 @@\n"
        " def get_user():\n"
        "+    return {'ok': True}\n"
    )

    pr.get_files.return_value = [
        changed_file,
        second_file,
    ]

    source.repo.get_pull.return_value = pr

    diff = source.fetch_pull_request_diff(102)

    assert (
        "diff --git a/backend/services/session_cache.py "
        "b/backend/services/session_cache.py"
    ) in diff

    assert (
        "-from redis import Redis"
        in diff
    )

    assert (
        "+from memcached import Client"
        in diff
    )

    assert (
        "diff --git a/backend/api/users.py "
        "b/backend/api/users.py"
    ) in diff


def test_files_without_patch_are_skipped():
    source = build_source()

    pr = MagicMock()

    deleted_or_binary_file = MagicMock()
    deleted_or_binary_file.filename = "image.png"
    deleted_or_binary_file.patch = None

    pr.get_files.return_value = [
        deleted_or_binary_file,
    ]

    source.repo.get_pull.return_value = pr

    diff = source.fetch_pull_request_diff(102)

    assert diff == ""


if __name__ == "__main__":
    test_fetch_pull_request()
    test_fetch_pull_request_diff()
    test_files_without_patch_are_skipped()

    print("All GitHub review source tests passed.")
