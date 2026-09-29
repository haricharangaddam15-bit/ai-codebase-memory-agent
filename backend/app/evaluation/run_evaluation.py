from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from backend.app.agents.qa_agent import QAAgent
from backend.app.memory.local_store import LocalMemoryStore


ROOT = Path(__file__).resolve().parents[3]
DATASET_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "why_questions.json"
)
MEMORY_FILE = ROOT / "data" / "memory" / "memories.json"
REPORT_DIR = Path(__file__).resolve().parent / "reports"
JSON_REPORT = REPORT_DIR / "evaluation-results.json"
MARKDOWN_REPORT = REPORT_DIR / "evaluation-report.md"


def load_dataset() -> dict[str, Any]:
    with DATASET_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def contains_evidence(memory: dict[str, Any]) -> bool:
    evidence = memory.get("evidence", {})
    quote = str(evidence.get("quote", "")).strip()
    source_url = str(evidence.get("source_url", "")).strip()
    return bool(quote and source_url)


def evaluate_memory_on(
    agent: QAAgent,
    item: dict[str, Any],
) -> dict[str, Any]:
    result = agent.ask(
        question=item["question"],
        memory_enabled=True,
    )

    expected = item["expected"]
    expected_type = expected["type"]

    documented_correct = (
        result.documented
        if expected_type == "documented"
        else not result.documented
    )

    memory_match = True
    citation_match = True
    evidence_present = True

    if expected_type == "documented":
        expected_title = expected["memory_title"]
        expected_source_id = expected["source_id"]

        memory_match = any(
            memory.get("title") == expected_title
            for memory in result.memories
        )

        citation_match = any(
            citation.get("source_id") == expected_source_id
            for citation in result.citations
        )

        evidence_present = all(
            contains_evidence(memory)
            for memory in result.memories
        )

    passed = (
        documented_correct
        and memory_match
        and citation_match
        and evidence_present
    )

    return {
        "id": item["id"],
        "question": item["question"],
        "expected": expected,
        "actual": {
            "documented": result.documented,
            "answer": result.answer,
            "memory_count": len(result.memories),
            "citation_count": len(result.citations),
            "memory_titles": [
                str(memory.get("title", ""))
                for memory in result.memories
            ],
            "citation_source_ids": [
                str(citation.get("source_id", ""))
                for citation in result.citations
            ],
        },
        "checks": {
            "documented_status": documented_correct,
            "memory_match": memory_match,
            "citation_match": citation_match,
            "evidence_present": evidence_present,
        },
        "passed": passed,
    }


def evaluate_memory_off(
    agent: QAAgent,
    item: dict[str, Any],
) -> dict[str, Any]:
    result = agent.ask(
        question=item["question"],
        memory_enabled=False,
    )

    no_memories = len(result.memories) == 0
    no_citations = len(result.citations) == 0
    disabled_message = (
        "memory is disabled" in result.answer.lower()
        and "no codebase memory was used" in result.answer.lower()
    )

    passed = no_memories and no_citations and disabled_message

    return {
        "id": item["id"],
        "question": item["question"],
        "actual": {
            "documented": result.documented,
            "answer": result.answer,
            "memory_count": len(result.memories),
            "citation_count": len(result.citations),
        },
        "checks": {
            "no_memories": no_memories,
            "no_citations": no_citations,
            "disabled_message": disabled_message,
        },
        "passed": passed,
    }


def build_summary(
    memory_on: list[dict[str, Any]],
    memory_off: list[dict[str, Any]],
) -> dict[str, Any]:
    on_passed = sum(item["passed"] for item in memory_on)
    off_passed = sum(item["passed"] for item in memory_off)

    documented_items = [
        item
        for item in memory_on
        if item["expected"]["type"] == "documented"
    ]
    not_documented_items = [
        item
        for item in memory_on
        if item["expected"]["type"] == "not_documented"
    ]

    documented_passed = sum(
        item["passed"] for item in documented_items
    )
    not_documented_passed = sum(
        item["passed"] for item in not_documented_items
    )

    return {
        "questions": len(memory_on),
        "memory_on_passed": on_passed,
        "memory_on_total": len(memory_on),
        "memory_off_passed": off_passed,
        "memory_off_total": len(memory_off),
        "documented_expected_passed": documented_passed,
        "documented_expected_total": len(documented_items),
        "not_documented_expected_passed": not_documented_passed,
        "not_documented_expected_total": len(not_documented_items),
        "all_passed": (
            on_passed == len(memory_on)
            and off_passed == len(memory_off)
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]

    lines = [
        "# AI Codebase Memory Agent Evaluation",
        "",
        "## Summary",
        "",
        f"- Questions: {summary['questions']}",
        (
            f"- Memory ON: "
            f"{summary['memory_on_passed']}/"
            f"{summary['memory_on_total']} passed"
        ),
        (
            f"- Memory OFF: "
            f"{summary['memory_off_passed']}/"
            f"{summary['memory_off_total']} passed"
        ),
        (
            f"- Documented questions: "
            f"{summary['documented_expected_passed']}/"
            f"{summary['documented_expected_total']} passed"
        ),
        (
            f"- Not documented questions: "
            f"{summary['not_documented_expected_passed']}/"
            f"{summary['not_documented_expected_total']} passed"
        ),
        f"- Overall: {'PASS' if summary['all_passed'] else 'FAIL'}",
        "",
        "## Memory ON",
        "",
    ]

    for item in report["memory_on"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.extend(
            [
                f"### {item['id']} — {status}",
                "",
                f"**Question:** {item['question']}",
                "",
                f"**Expected:** `{item['expected']['type']}`",
                "",
                f"**Documented:** `{item['actual']['documented']}`",
                "",
                f"**Memories:** {item['actual']['memory_titles']}",
                "",
                f"**Citations:** {item['actual']['citation_source_ids']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Memory OFF",
            "",
        ]
    )

    for item in report["memory_off"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.extend(
            [
                f"### {item['id']} — {status}",
                "",
                f"**Question:** {item['question']}",
                "",
                f"**Memories used:** {item['actual']['memory_count']}",
                "",
                f"**Citations:** {item['actual']['citation_count']}",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    dataset = load_dataset()

    store = LocalMemoryStore(str(MEMORY_FILE))
    agent = QAAgent(store)

    questions = dataset["questions"]

    memory_on = [
        evaluate_memory_on(agent, item)
        for item in questions
    ]

    memory_off = [
        evaluate_memory_off(agent, item)
        for item in questions
    ]

    report = {
        "version": 1,
        "dataset_version": dataset.get("version"),
        "memory_file": str(MEMORY_FILE),
        "memory_count": len(store.load()),
        "summary": build_summary(memory_on, memory_off),
        "memory_on": memory_on,
        "memory_off": memory_off,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    JSON_REPORT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    MARKDOWN_REPORT.write_text(
        render_markdown(report),
        encoding="utf-8",
    )

    summary = report["summary"]

    print("===== AI CODEBASE MEMORY EVALUATION =====")
    print(f"Questions: {summary['questions']}")
    print(
        f"Memory ON: "
        f"{summary['memory_on_passed']}/"
        f"{summary['memory_on_total']} passed"
    )
    print(
        f"Memory OFF: "
        f"{summary['memory_off_passed']}/"
        f"{summary['memory_off_total']} passed"
    )
    print(
        f"Documented: "
        f"{summary['documented_expected_passed']}/"
        f"{summary['documented_expected_total']} passed"
    )
    print(
        f"Not documented: "
        f"{summary['not_documented_expected_passed']}/"
        f"{summary['not_documented_expected_total']} passed"
    )
    print(
        f"Overall: {'PASS' if summary['all_passed'] else 'FAIL'}"
    )
    print()
    print(f"JSON report: {JSON_REPORT}")
    print(f"Markdown report: {MARKDOWN_REPORT}")

    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
