import re
from pathlib import Path


class PRReviewAgent:
    """
    Reviews a PR against documented engineering memories.

    A review comment is produced only when:
    - the memory is active,
    - the memory contains evidence,
    - the changed file is linked to the memory,
    - the documented choice is removed/replaced in the diff.

    The agent never invents undocumented rationale.
    """

    MAX_COMMENTS = 5

    _STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by",
        "for", "from", "in", "is", "it", "of", "on", "or",
        "the", "this", "to", "use", "used", "using", "we",
        "with", "choose", "chosen", "selected", "decision",
        "architecture", "session", "cache", "backend",
    }

    _TECHNOLOGIES = {
        "redis",
        "memcached",
        "postgresql",
        "postgres",
        "mysql",
        "sqlite",
        "mongodb",
        "mongo",
        "fastapi",
        "flask",
        "django",
        "express",
        "next",
    }

    def review(
        self,
        diff: str,
        memories: list[dict],
    ) -> list[dict]:
        if not diff.strip():
            return []

        changed_files = self._extract_changed_files(diff)

        if not changed_files:
            return []

        comments: list[dict] = []

        for memory in memories:
            if len(comments) >= self.MAX_COMMENTS:
                break

            if memory.get("status") != "active":
                continue

            if memory.get("superseded_by"):
                continue

            evidence = memory.get("evidence", {})

            if not evidence.get("quote", "").strip():
                continue

            if not self._memory_relevant(memory, changed_files):
                continue

            if not self._conflicts_with_decision(diff, memory):
                continue

            comment = self._build_comment(memory)

            if comment:
                comments.append(comment)

        return comments[: self.MAX_COMMENTS]

    def _extract_changed_files(self, diff: str) -> set[str]:
        files: set[str] = set()

        for match in re.finditer(
            r"^diff --git a/(.+?) b/(.+?)$",
            diff,
            flags=re.MULTILINE,
        ):
            old_path = match.group(1).strip()
            new_path = match.group(2).strip()

            if old_path != "/dev/null":
                files.add(old_path)

            if new_path != "/dev/null":
                files.add(new_path)

        for match in re.finditer(
            r"^---\s+(?:a/)?(.+)$",
            diff,
            flags=re.MULTILINE,
        ):
            path_value = match.group(1).strip()
            if path_value != "/dev/null":
                files.add(path_value)

        for match in re.finditer(
            r"^\+\+\+\s+(?:b/)?(.+)$",
            diff,
            flags=re.MULTILINE,
        ):
            path_value = match.group(1).strip()
            if path_value != "/dev/null":
                files.add(path_value)

        for match in re.finditer(
            r"^rename from (.+)$",
            diff,
            flags=re.MULTILINE,
        ):
            files.add(match.group(1).strip())

        for match in re.finditer(
            r"^rename to (.+)$",
            diff,
            flags=re.MULTILINE,
        ):
            files.add(match.group(1).strip())

        return files

    def _memory_relevant(
        self,
        memory: dict,
        changed_files: set[str],
    ) -> bool:
        memory_paths = memory.get("file_paths", [])

        if not memory_paths:
            return False

        for changed in changed_files:
            changed_path = Path(changed)

            for memory_path in memory_paths:
                stored_path = Path(memory_path)

                if changed == memory_path:
                    return True

                if changed_path == stored_path:
                    return True


        return False

    def _conflicts_with_decision(
        self,
        diff: str,
        memory: dict,
    ) -> bool:
        decision_terms = self._decision_terms(memory)

        if not decision_terms:
            return False

        deleted_text = " ".join(
            self._deleted_lines(diff)
        ).lower()

        added_text = " ".join(
            self._added_lines(diff)
        ).lower()

        if not deleted_text:
            return False

        documented_choices = {
            term
            for term in decision_terms
            if term in self._TECHNOLOGIES
        }

        if not documented_choices:
            return False

        # The documented technology/choice must actually disappear
        # from the implementation.
        removed_choices = {
            technology
            for technology in documented_choices
            if re.search(
                rf"\b{re.escape(technology)}\b",
                deleted_text,
            )
        }

        if not removed_choices:
            return False

        # A deleted implementation file removes the documented choice
        # entirely, so no added replacement lines are required.
        deleted_file = bool(
            re.search(
                r"^\+\+\+\s+/dev/null$",
                diff,
                flags=re.MULTILINE,
            )
        )

        if deleted_file:
            return True

        # There must be evidence that the implementation is moving
        # toward another choice or explicitly replacing the old one.
        replacement_signals = (
            "replace",
            "replaced",
            "instead of",
            "switch",
            "switched",
            "migrate",
            "migration",
            "remove",
            "removed",
            "drop",
            "dropped",
        )

        explicit_replacement = any(
            signal in added_text
            for signal in replacement_signals
        )

        added_technologies = {
            technology
            for technology in self._TECHNOLOGIES
            if technology not in removed_choices
            and re.search(
                rf"\b{re.escape(technology)}\b",
                added_text,
            )
        }

        # A different technology being introduced alongside removal
        # of the documented choice is sufficient evidence.
        technology_replacement = bool(added_technologies)

        return explicit_replacement or technology_replacement

    def _decision_terms(self, memory: dict) -> set[str]:
        text = " ".join(
            [
                memory.get("title", ""),
                memory.get("rationale", ""),
                memory.get("summary", ""),
            ]
        )

        tokens = re.findall(
            r"[a-z0-9][a-z0-9._-]*",
            text.lower(),
        )

        return {
            token
            for token in tokens
            if token not in self._STOPWORDS
            and len(token) >= 3
        }

    def _added_lines(self, diff: str) -> list[str]:
        return [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("+")
            and not line.startswith("+++")
        ]

    def _deleted_lines(self, diff: str) -> list[str]:
        return [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("-")
            and not line.startswith("---")
        ]

    def _build_comment(self, memory: dict) -> dict | None:
        evidence = memory.get("evidence", {})

        quote = evidence.get("quote", "").strip()
        source_url = evidence.get("source_url", "").strip()

        if not quote or not source_url:
            return None

        title = memory.get(
            "title",
            "Documented engineering decision",
        )

        rationale = memory.get(
            "rationale",
            "not documented",
        ).strip()

        return {
            "severity": "warning",
            "title": f"Check documented decision: {title}",
            "body": (
                "This change appears to conflict with a documented "
                "engineering decision.\n\n"
                f"Documented rationale: {rationale}\n\n"
                f"Evidence: {quote}"
            ),
            "memory_title": title,
            "evidence_quote": quote,
            "source_url": source_url,
            "source_type": evidence.get(
                "source_type",
                "github",
            ),
            "source_id": evidence.get(
                "source_id",
                "",
            ),
        }
