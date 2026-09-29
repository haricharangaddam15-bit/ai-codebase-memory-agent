class QAAgent:
    """
    Answers questions from retrieved team memories.

    The agent must distinguish:
      - documented team history
      - generic explanation
      - missing rationale
    """

    def answer(self, question: str, *, memory_enabled: bool = True) -> dict:
        if not memory_enabled:
            return {
                "answer": "Generic answer mode is not implemented yet.",
                "memories_used": [],
                "memory_enabled": False,
            }

        return {
            "answer": "Memory-backed Q&A will be implemented next.",
            "memories_used": [],
            "memory_enabled": True,
        }
