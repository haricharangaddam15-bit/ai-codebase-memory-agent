from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from backend.app.agents.extractor import (
    RuleBasedDecisionExtractor,
    memory_to_json,
)
from backend.app.ingestion.github_source import GitHubSource
from backend.app.ingestion.pipeline import IngestionPipeline


ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")


def get_github_token() -> str:
    token = os.getenv("GITHUB_TOKEN", "").strip()

    if token:
        return token

    result = subprocess.run(
        ["gh", "auth", "token"],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def main() -> None:
    token = get_github_token()
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()

    if not repository:
        raise SystemExit(
            "GITHUB_REPOSITORY is missing from .env"
        )

    print("===== GITHUB INGESTION =====")
    print(f"Repository: {repository}")
    print()

    source = GitHubSource(
        token=token,
        repository=repository,
    )

    prs = source.fetch_pull_requests(limit=50)

    print(f"PRs fetched: {len(prs)}")
    print()

    if not prs:
        print("No pull requests found.")
        return

    for pr in prs:
        print(
            f"PR #{pr.number}: {pr.title} "
            f"| comments={len(pr.comments)} "
            f"| files={len(pr.changed_files)}"
        )

    print()
    print("===== RUNNING PIPELINE =====")

    pipeline = IngestionPipeline(
        extractor=RuleBasedDecisionExtractor()
    )

    result = pipeline.process(prs)

    print(f"Input PRs:       {result.input_count}")
    print(f"High-signal PRs: {result.selected_count}")
    print(f"Skipped PRs:     {result.skipped_count}")
    print(f"Memories:        {result.memory_count}")
    print(f"Errors:          {len(result.errors)}")

    print()
    print("===== EXTRACTED MEMORIES =====")

    for memory in result.memories:
        print()
        print(
            json.dumps(
                memory_to_json(memory),
                indent=2,
                ensure_ascii=False,
            )
        )

    if result.errors:
        print()
        print("===== ERRORS =====")

        for error in result.errors:
            print(error)


if __name__ == "__main__":
    main()
