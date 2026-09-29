from backend.app.schemas.ingestion import PRSource


HIGH_SIGNAL_TERMS = (
    "instead of",
    "we tried",
    "we decided",
    "because",
    "trade-off",
    "tradeoff",
    "rejected",
    "architecture",
    "breaking",
    "decision",
    "why",
)


def is_high_signal(pr: PRSource) -> bool:
    text = f"{pr.title}\n{pr.body}\n" + "\n".join(pr.comments)
    text = text.lower()

    return any(term in text for term in HIGH_SIGNAL_TERMS)


def filter_prs(prs: list[PRSource]) -> tuple[list[PRSource], list[PRSource]]:
    selected = []
    skipped = []

    for pr in prs:
        if is_high_signal(pr):
            selected.append(pr)
        else:
            skipped.append(pr)

    return selected, skipped
