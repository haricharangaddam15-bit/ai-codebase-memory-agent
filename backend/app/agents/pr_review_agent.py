class PRReviewAgent:
    """
    Checks a PR against grounded project memories.

    Reviews will be limited to a small number of evidence-backed comments.
    """

    MAX_COMMENTS = 5

    def review(self, diff: str, memories: list[dict]) -> list[dict]:
        return []
