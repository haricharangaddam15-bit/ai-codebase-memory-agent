from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
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


def github_token() -> str:
    token = os.getenv("GITHUB_TOKEN", "").strip()

    if token:
        return token

    return subprocess.run(
        ["gh", "auth", "token"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main() -> None:
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()

    if not repository:
        raise SystemExit("GITHUB_REPOSITORY is missing")

    source = GitHubSource(
        github_token(),
        repository,
    )

    prs = source.fetch_pull_requests(limit=50)

    pipeline = IngestionPipeline(
        extractor=RuleBasedDecisionExtractor()
    )

    result = pipeline.process(prs)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "statistics": {
            "input_prs": result.input_count,
            "high_signal_prs": result.selected_count,
            "skipped_prs": result.skipped_count,
            "memories": result.memory_count,
            "errors": len(result.errors),
        },
        "memories": [
            memory_to_json(memory)
            for memory in result.memories
        ],
        "errors": result.errors,
    }

    output_path = (
        ROOT
        / "data"
        / "processed"
        / "ingestion.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    print(f"Saved: {output_path}")
    print(
        f"Memories saved: {len(result.memories)}"
    )


if __name__ == "__main__":
    main()
