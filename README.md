# AI Codebase Memory Agent

An AI-powered long-term memory for software projects.

The agent remembers:

- what was decided
- why it was decided
- alternatives that were rejected
- project conventions
- bugs and incidents
- recurring review feedback
- technical debt

Every grounded memory must contain evidence pointing back to project history.

## Architecture

GitHub PRs / Issues / ADRs / Docs / Postmortems
        |
        v
Signal Filter
        |
        v
LLM Extraction
        |
        v
Evidence Validation
        |
        v
Code Linking
        |
        v
Hindsight Memory
        |
        +----> Q&A Agent ----> Chat UI
        |
        +----> PR Review Agent ----> GitHub Action
        |
        +----> Capture Agent ----> Confirm to Save

## MVP

1. Ingest high-signal GitHub PRs.
2. Extract typed decision records.
3. Store them in Hindsight.
4. Answer why-questions with citations.
5. Compare memory ON vs OFF.
6. Capture new decisions.
7. Review PRs using grounded memories.
8. Demonstrate the 20-interaction learning curve.
