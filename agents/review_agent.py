"""
Review Agent - evaluates a PR against its spec and acceptance criteria.
Gives a structured verdict: approved or request changes.
"""
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from anthropic import Anthropic
from config import Config

REVIEW_SYSTEM_PROMPT = """You are a senior software engineer performing a code review for a spec-driven Next.js project.

Your job is to evaluate whether a PR correctly implements the user story specification.

You will be given:
1. The user story spec (acceptance criteria, tasks, definition of done)
2. The PR diff (files added/changed with their patches)

Evaluate thoroughly but fairly. The goal is to ship working software, not perfect software.

Return ONLY valid JSON — no markdown, no explanation. Structure:
{
  "verdict": "approved" | "request_changes",
  "summary": "2-3 sentence overall assessment of the implementation",
  "ac_review": [
    {
      "criterion": "AC-1: name of criterion",
      "status": "implemented" | "partial" | "missing",
      "comment": "specific, actionable feedback"
    }
  ],
  "issues": [
    "Specific issue that must be fixed before merging (only if verdict is request_changes)"
  ],
  "strengths": [
    "Something done well in this implementation"
  ],
  "email_summary": "A short, non-technical paragraph for the Product Owner summarising what was built, written in plain language. Mention the feature name and what users can now do."
}

Be decisive — only request changes for real problems, not nitpicks.
"""

REVIEW_PROMPT = """
Review this PR against the spec below.

=== USER STORY SPEC ===
{spec}

=== PR DIFF ===
{diff}

Return your review as valid JSON only.
"""


class ReviewAgent:
    def __init__(self, config: Config):
        self.client = Anthropic(api_key=config.anthropic_api_key, max_retries=5)
        self.model = config.claude_model
        self.config = config

    def _call(self, system: str, user: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text.strip()

    def _parse_json(self, raw: str) -> dict:
        raw = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"^```\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        return json.loads(raw.strip())

    def review_pr(self, spec: str, diff: str) -> dict:
        """Evaluate a PR against its spec. Returns structured review dict."""
        prompt = REVIEW_PROMPT.format(spec=spec, diff=diff)
        raw = self._call(REVIEW_SYSTEM_PROMPT, prompt)
        return self._parse_json(raw)

    def send_email_summary(self, story_title: str, review: dict) -> bool:
        """
        Send a PO summary email via Gmail SMTP.
        Returns True if sent successfully, False otherwise.
        """
        if not all([self.config.gmail_app_password, self.config.gmail_sender, self.config.po_email]):
            return False

        subject = f"✅ Story completed: {story_title}"
        body = f"""Hi,

A new feature has been completed and deployed.

{review.get('email_summary', '')}

---
Story: {story_title}
Review: {review.get('summary', '')}

This summary was generated automatically by the Developer Agent.
"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.gmail_sender
            msg["To"] = self.config.po_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.config.gmail_sender, self.config.gmail_app_password)
                server.sendmail(self.config.gmail_sender, self.config.po_email, msg.as_string())
            return True
        except Exception:
            return False
