from pathlib import Path
from unittest.mock import patch

from scripts import run_github_pr_review


def test_runner_writes_no_findings_summary(tmp_path):
    memory_file = tmp_path / "memories.json"
    result_file = tmp_path / "review-result.md"

    memory_file.write_text(
        '{"version":1,"memory_count":0,"memories":[]}',
        encoding="utf-8",
    )

    fake_pr = type(
        "FakePR",
        (),
        {
            "number": 1,
            "title": "Test PR",
            "changed_files": ["test.py"],
        },
    )()

    with patch.object(
        run_github_pr_review,
        "MEMORY_FILE",
        memory_file,
    ), patch.object(
        run_github_pr_review,
        "RESULT_FILE",
        result_file,
    ), patch.object(
        run_github_pr_review,
        "GitHubSource",
    ) as source_class:
        source = source_class.return_value
        source.fetch_pull_request.return_value = fake_pr
        source.fetch_pull_request_diff.return_value = (
            "diff --git a/test.py b/test.py\n"
            "--- a/test.py\n"
            "+++ b/test.py\n"
            "@@ -1 +1 @@\n"
            "+print('hello')\n"
        )

        with patch.dict(
            "os.environ",
            {
                "GITHUB_TOKEN": "test-token",
                "GITHUB_REPOSITORY": "owner/repo",
                "PR_NUMBER": "1",
            },
            clear=False,
        ):
            run_github_pr_review.main()

    content = result_file.read_text(
        encoding="utf-8"
    )

    assert "No evidence-backed review comments." in content
    assert "Report-only mode" in content


if __name__ == "__main__":
    test_runner_writes_no_findings_summary()
    print("GitHub PR review runner test passed.")
