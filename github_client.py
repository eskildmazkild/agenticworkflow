"""
GitHub API client for spec-agent.
Handles creating Issues, labels, committing spec files, and dev workflow.
"""
import base64
import re
from dataclasses import dataclass
from typing import Optional

from github import Github, GithubException

from config import Config


def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text[:50]


@dataclass
class CreatedEpic:
    issue_number: int
    issue_url: str
    slug: str


@dataclass
class CreatedStory:
    issue_number: int
    issue_url: str
    slug: str


@dataclass
class ReadyStory:
    issue_number: int
    title: str
    url: str
    epic_number: Optional[int]
    slug: str


class GitHubClient:
    def __init__(self, config: Config):
        self.config = config
        self.gh = Github(config.github_token)
        self.repo = self.gh.get_repo(config.github_repo)
        # Separate repo for code/PRs (e.g. subscription-tool vs agenticworkflow)
        self.code_repo = self.gh.get_repo(config.github_code_repo)
        self._ensure_labels()

    def _ensure_labels(self):
        """Create required labels if they don't exist."""
        required_labels = [
            {"name": "epic",          "color": "7057ff", "description": "Epic - high level feature"},
            {"name": "user-story",    "color": "0075ca", "description": "User story"},
            {"name": "spec-draft",    "color": "e4e669", "description": "Spec awaiting review"},
            {"name": "spec-approved", "color": "0e8a16", "description": "Spec reviewed and approved"},
            {"name": "in-progress",   "color": "fbca04", "description": "Currently being developed"},
            {"name": "in-review",     "color": "e11d48", "description": "PR open, awaiting review"},
            {"name": "done",          "color": "22c55e", "description": "Completed and deployed"},
        ]
        existing = {label.name for label in self.repo.get_labels()}
        for label in required_labels:
            if label["name"] not in existing:
                try:
                    self.repo.create_label(
                        name=label["name"],
                        color=label["color"],
                        description=label["description"],
                    )
                except GithubException:
                    pass

    # ── Phase 1: Spec creation ──────────────────────────────────────────────────

    def create_epic_issue(self, title: str, epic_markdown: str) -> CreatedEpic:
        issue = self.repo.create_issue(
            title=f"[EPIC] {title}",
            body=epic_markdown,
            labels=["epic", "spec-approved"],
        )
        return CreatedEpic(
            issue_number=issue.number,
            issue_url=issue.html_url,
            slug=slugify(title),
        )

    def create_story_issue(self, title: str, story_markdown: str, epic_issue_number: int) -> CreatedStory:
        body = f"**Part of epic:** #{epic_issue_number}\n\n---\n\n{story_markdown}"
        issue = self.repo.create_issue(
            title=f"[STORY] {title}",
            body=body,
            labels=["user-story", "spec-approved"],
        )
        return CreatedStory(
            issue_number=issue.number,
            issue_url=issue.html_url,
            slug=slugify(title),
        )

    def create_spec_files(self, epic_title: str, epic_markdown: str, stories: list[dict], epic_issue_number: int):
        epic_slug = slugify(epic_title)
        folder = f"{self.config.specs_folder}/epic-{epic_issue_number}-{epic_slug}"

        self._commit_file(
            path=f"{folder}/epic.md",
            content=f"<!-- GitHub Issue: #{epic_issue_number} -->\n\n" + epic_markdown,
            message=f"docs: add epic spec - {epic_title} (#{epic_issue_number})",
        )
        for story in stories:
            story_slug = slugify(story["title"])
            self._commit_file(
                path=f"{folder}/story-{story_slug}.md",
                content=f"<!-- GitHub Issue: #{story['issue_number']} -->\n<!-- Part of Epic: #{epic_issue_number} -->\n\n" + story["content"],
                message=f"docs: add story spec - {story['title']} (#{story['issue_number']})",
            )

    # ── Phase 2: Developer workflow ─────────────────────────────────────────────

    def list_ready_stories(self) -> list[ReadyStory]:
        """List stories that are approved and not yet started."""
        issues = self.repo.get_issues(
            labels=["user-story", "spec-approved"],
            state="open",
        )
        result = []
        for issue in issues:
            label_names = {l.name for l in issue.labels}
            if "in-progress" not in label_names and "in-review" not in label_names:
                result.append(ReadyStory(
                    issue_number=issue.number,
                    title=issue.title.replace("[STORY] ", ""),
                    url=issue.html_url,
                    epic_number=self._extract_epic_number(issue.body or ""),
                    slug=slugify(issue.title.replace("[STORY] ", "")),
                ))
        result.sort(key=lambda s: s.issue_number)
        return result

    def get_spec_content(self, epic_number: int, story_slug: str) -> str:
        """Read the spec markdown file for a story from GitHub."""
        # Find the epic folder — search specs/ for a folder matching epic-{number}-*
        try:
            contents = self.repo.get_contents(self.config.specs_folder, ref=self.config.github_branch)
        except GithubException:
            return ""

        epic_folder = None
        for item in contents:
            if item.type == "dir" and item.name.startswith(f"epic-{epic_number}-"):
                epic_folder = item.path
                break

        if not epic_folder:
            return ""

        # Find story file matching the slug
        try:
            story_contents = self.repo.get_contents(epic_folder, ref=self.config.github_branch)
        except GithubException:
            return ""

        for item in story_contents:
            if item.type == "file" and story_slug in item.name:
                return item.decoded_content.decode("utf-8")

        return ""

    def mark_in_progress(self, issue_number: int):
        """Move a story to in-progress."""
        issue = self.repo.get_issue(issue_number)
        issue.add_to_labels("in-progress")
        try:
            issue.remove_from_labels("spec-approved")
        except GithubException:
            pass

    def mark_in_review(self, issue_number: int, pr_url: str, branch: str):
        """Move a story to in-review and link the PR."""
        issue = self.repo.get_issue(issue_number)
        issue.add_to_labels("in-review")
        try:
            issue.remove_from_labels("in-progress")
        except GithubException:
            pass
        issue.create_comment(
            f"🔍 **PR ready for review:** {pr_url}\n\nBranch: `{branch}`"
        )

    def create_pull_request(self, title: str, body: str, branch: str) -> str:
        """Create a PR and return its URL."""
        pr = self.code_repo.create_pull(
            title=title,
            body=body,
            head=branch,
            base=self.config.github_branch,
        )
        return pr.html_url

    # ── Phase 3: Review workflow ────────────────────────────────────────────────

    def list_in_review_stories(self) -> list[ReadyStory]:
        """List stories currently in-review (PR open, awaiting review)."""
        issues = self.repo.get_issues(labels=["user-story", "in-review"], state="open")
        result = []
        for issue in issues:
            result.append(ReadyStory(
                issue_number=issue.number,
                title=issue.title.replace("[STORY] ", ""),
                url=issue.html_url,
                epic_number=self._extract_epic_number(issue.body or ""),
                slug=slugify(issue.title.replace("[STORY] ", "")),
            ))
        return result

    def get_pr_for_issue(self, issue_number: int) -> Optional[object]:
        """Find the open PR linked to an issue number.

        Searches (in order):
          1. PR body   — looks for #N as a whole number (e.g. 'Closes #8', not '#18')
          2. PR title  — looks for #N as a whole number (e.g. 'feat: ... (#8)')
          3. Branch    — branch name ends with -N  (e.g. feature/add-subscription-8)
        """
        open_prs = list(self.code_repo.get_pulls(state="open"))
        # Word-boundary regex so #8 doesn't match #18, #28, etc.
        pattern = re.compile(rf"#{issue_number}\b")
        for pr in open_prs:
            body   = pr.body or ""
            title  = pr.title or ""
            branch = pr.head.ref or ""
            body_match   = bool(pattern.search(body))
            title_match  = bool(pattern.search(title))
            branch_match = branch.endswith(f"-{issue_number}")
            if body_match or title_match or branch_match:
                return pr
        return None

    def get_pr_diff(self, pr_number: int) -> str:
        """Get changed files and their patches for a PR."""
        pr = self.code_repo.get_pull(pr_number)
        sections = [f"PR: {pr.title}\n"]
        for f in pr.get_files():
            sections.append(f"--- {f.filename} ({f.status}, +{f.additions}/-{f.deletions}) ---")
            if f.patch:
                sections.append(f.patch)
        return "\n".join(sections)

    def post_pr_review(self, pr_number: int, body: str, approve: bool):
        """Post a review on a PR — approve or request changes."""
        pr = self.code_repo.get_pull(pr_number)
        event = "APPROVE" if approve else "REQUEST_CHANGES"
        pr.create_review(body=body, event=event)

    def merge_pr(self, pr_number: int, commit_message: str):
        """Merge a PR with a squash commit."""
        pr = self.code_repo.get_pull(pr_number)
        pr.merge(commit_message=commit_message, merge_method="squash")

    def mark_done(self, issue_number: int):
        """Close the issue and move it to done."""
        issue = self.repo.get_issue(issue_number)
        issue.add_to_labels("done")
        try:
            issue.remove_from_labels("in-review")
        except GithubException:
            pass
        issue.edit(state="closed")

    def reopen_for_changes(self, issue_number: int):
        """Send a story back to in-progress after review requests changes."""
        issue = self.repo.get_issue(issue_number)
        issue.add_to_labels("in-progress")
        try:
            issue.remove_from_labels("in-review")
        except GithubException:
            pass

    # ── Shared helpers ──────────────────────────────────────────────────────────

    def _extract_epic_number(self, body: str) -> Optional[int]:
        match = re.search(r"Part of epic.*?#(\d+)", body, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _commit_file(self, path: str, content: str, message: str):
        try:
            existing = self.repo.get_contents(path, ref=self.config.github_branch)
            self.repo.update_file(
                path=path,
                message=message,
                content=content,
                sha=existing.sha,
                branch=self.config.github_branch,
            )
        except GithubException as e:
            if e.status == 404:
                self.repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=self.config.github_branch,
                )
            else:
                raise
