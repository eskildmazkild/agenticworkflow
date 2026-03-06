"""
Configuration loader for spec-agent.
Reads from .env file in the same directory as the script.
"""
import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    def __init__(
        self,
        anthropic_api_key: str,
        github_token: str,
        github_repo: str,
        github_code_repo: str = "",
        github_branch: str = "main",
        specs_folder: str = "specs",
        claude_model: str = "claude-sonnet-4-6",
        project_local_path: str = "",
        po_email: str = "",
        gmail_sender: str = "",
        gmail_app_password: str = "",
    ):
        self.anthropic_api_key = anthropic_api_key
        self.github_token = github_token
        self.github_repo = github_repo
        # Repo where code/PRs live — defaults to github_repo if not set separately
        self.github_code_repo = github_code_repo or github_repo
        self.github_branch = github_branch
        self.specs_folder = specs_folder
        self.claude_model = claude_model
        self.project_local_path = project_local_path
        self.po_email = po_email
        self.gmail_sender = gmail_sender
        self.gmail_app_password = gmail_app_password

    @classmethod
    def load(cls) -> "Config":
        """Load config from .env file. Raises clear errors if required vars are missing."""
        env_path = Path(__file__).parent / ".env"
        load_dotenv(dotenv_path=env_path)

        missing = []

        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            missing.append("GITHUB_TOKEN")

        github_repo = os.getenv("GITHUB_REPO")
        if not github_repo:
            missing.append("GITHUB_REPO")

        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Copy .env.example to .env and fill in the values."
            )

        return cls(
            anthropic_api_key=anthropic_api_key,
            github_token=github_token,
            github_repo=github_repo,
            github_code_repo=os.getenv("GITHUB_CODE_REPO", ""),
            github_branch=os.getenv("GITHUB_BRANCH", "main"),
            specs_folder=os.getenv("SPECS_FOLDER", "specs"),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
            project_local_path=os.getenv("PROJECT_LOCAL_PATH", ""),
            po_email=os.getenv("PO_EMAIL", ""),
            gmail_sender=os.getenv("GMAIL_SENDER", ""),
            gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        )
