from github import Github

from backend.app.schemas.ingestion import PRSource


class GitHubSource:
    def __init__(self, token: str, repository: str):
        if not token:
            raise ValueError("GITHUB_TOKEN is required.")

        if not repository:
            raise ValueError("GITHUB_REPOSITORY is required.")

        self.github = Github(token)
        self.repo = self.github.get_repo(repository)

    def fetch_pull_request(self, number: int) -> PRSource:
        """Fetch one pull request with its metadata and changed files."""

        pr = self.repo.get_pull(number)

        comments = [
            comment.body or ""
            for comment in pr.get_issue_comments()
        ]

        review_comments = [
            comment.body or ""
            for comment in pr.get_review_comments()
        ]

        files = [
            file.filename
            for file in pr.get_files()
        ]

        return PRSource(
            number=pr.number,
            title=pr.title,
            body=pr.body or "",
            url=pr.html_url,
            author=pr.user.login if pr.user else "",
            state=pr.state,
            merged=pr.merged,
            created_at=pr.created_at.isoformat(),
            updated_at=pr.updated_at.isoformat(),
            changed_files=files,
            comments=comments + review_comments,
        )

    def fetch_pull_request_diff(self, number: int) -> str:
        """Build a unified diff from the pull request's changed files."""

        pr = self.repo.get_pull(number)

        diff_parts: list[str] = []

        for file in pr.get_files():
            filename = file.filename
            patch = getattr(file, "patch", None)

            if not patch:
                continue

            diff_parts.append(
                f"diff --git a/{filename} b/{filename}\n"
                f"--- a/{filename}\n"
                f"+++ b/{filename}\n"
                f"{patch}\n"
            )

        return "".join(diff_parts)

    def fetch_pull_requests(self, limit: int = 50) -> list[PRSource]:
        results: list[PRSource] = []

        for pr in self.repo.get_pulls(
            state="all",
            sort="updated",
            direction="desc",
        ):
            if len(results) >= limit:
                break

            comments = [
                comment.body or ""
                for comment in pr.get_issue_comments()
            ]

            review_comments = [
                comment.body or ""
                for comment in pr.get_review_comments()
            ]

            files = [
                file.filename
                for file in pr.get_files()
            ]

            results.append(
                PRSource(
                    number=pr.number,
                    title=pr.title,
                    body=pr.body or "",
                    url=pr.html_url,
                    author=pr.user.login if pr.user else "",
                    state=pr.state,
                    merged=pr.merged,
                    created_at=pr.created_at.isoformat(),
                    updated_at=pr.updated_at.isoformat(),
                    changed_files=files,
                    comments=comments + review_comments,
                )
            )

        return results
