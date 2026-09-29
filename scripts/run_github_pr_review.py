from __future__ import annotations

import os
from pathlib import Path

from backend.app.agents.pr_review_agent import PRReviewAgent
from backend.app.ingestion.github_source import GitHubSource
from backend.app.memory.local_store import LocalMemoryStore


ROOT = Path(__file__).resolve().parents[1]

MEMORY_FILE = (
    ROOT
    / "data"
    / "memory"
    / "memories.json"
)

RESULT_FILE = ROOT / "review-result.md"


def main() -> None:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    pr_number_raw = os.getenv("PR_NUMBER", "").strip()

    if not token:
        raise SystemExit("GITHUB_TOKEN is missing.")

    if not repository:
        raise SystemExit("GITHUB_REPOSITORY is missing.")

    if not pr_number_raw:
        raise SystemExit("PR_NUMBER is missing.")

    try:
        pr_number = int(pr_number_raw)
    except ValueError as exc:
        raise SystemExit(
            "PR_NUMBER must be an integer."
        ) from exc

    print("===== AI CODEBASE MEMORY PR REVIEW =====")
    print(f"Repository: {repository}")
    print(f"PR number:  {pr_number}")
    print()

    source = GitHubSource(
        token=token,
        repository=repository,
    )

    pr = source.fetch_pull_request(pr_number)
    diff = source.fetch_pull_request_diff(pr_number)

    print(f"PR title:       {pr.title}")
    print(f"Changed files:  {len(pr.changed_files)}")
    print(f"Diff size:      {len(diff)} characters")
    print()

    memory_store = LocalMemoryStore(
        str(MEMORY_FILE)
    )

    memories = memory_store.load()

    print(f"Memories loaded: {len(memories)}")
    print()

    agent = PRReviewAgent()

    comments = agent.review(
        diff=diff,
        memories=memories,
    )

    lines = [
        "## AI Codebase Memory PR Review",
        "",
        f"**PR:** #{pr.number} — {pr.title}",
        "",
        f"**Changed files:** {len(pr.changed_files)}",
        "",
        f"**Documented memories loaded:** {len(memories)}",
        "",
    ]

    if not comments:
        print("Result: no evidence-backed review comments.")
        print()

        lines.extend(
            [
                "### Result",
                "",
                "No evidence-backed review comments.",
                "",
            ]
        )
    else:
        print(
            f"Result: {len(comments)} "
            "evidence-backed comment(s)."
        )
        print()

        lines.extend(
            [
                f"### Findings ({len(comments)})",
                "",
            ]
        )

        for index, comment in enumerate(
            comments,
            start=1,
        ):
            print(
                f"[{index}] "
                f"{comment['title']}"
            )
            print(comment["body"])
            print()
            print(
                f"Evidence source: "
                f"{comment['source_url']}"
            )
            print()

            lines.extend(
                [
                    f"#### {index}. {comment['title']}",
                    "",
                    comment["body"],
                    "",
                    "**Evidence source:** "
                    f"{comment['source_url']}",
                    "",
                ]
            )

    lines.extend(
        [
            "---",
            "",
            "Report-only mode: no GitHub review comment "
            "was posted automatically.",
            "",
        ]
    )

    RESULT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Summary written to: {RESULT_FILE}")


if __name__ == "__main__":
    main()
