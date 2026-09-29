class CaptureAgent:
    """
    Drafts a decision record from newly observed project history.
    """

    def draft(self, source_text: str) -> dict:
        return {
            "status": "draft",
            "message": "Decision capture will be implemented next.",
            "source_length": len(source_text),
        }
