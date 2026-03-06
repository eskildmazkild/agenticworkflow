"""
Developer Agent - reads a user story spec and implements it in a Next.js project.
Scaffolds the project if it doesn't exist yet, generates code, and verifies the build.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from config import Config

DEVELOPER_SYSTEM_PROMPT = """You are a senior fullstack developer implementing features for a Next.js 14 web application called "Subscription Management Tool".

Tech stack:
- Next.js 14 with App Router
- TypeScript (strict mode — no implicit `any`)
- Tailwind CSS for styling
- Prisma ORM with SQLite for the database (prisma + @prisma/client)
- shadcn/ui for UI components
- Playwright for e2e testing (tests live in e2e/)

Architecture rules:
- Use Server Components by default. Only use "use client" when you need useState, useEffect, or event handlers.
- Database access only in Server Components or API route handlers — never in Client Components.
- Keep Prisma client in lib/prisma.ts (singleton). Schema in prisma/schema.prisma.
- All TypeScript types/interfaces go in lib/types.ts.
- Components live in components/. Page files live in app/.
- When using Prisma for the first time, include prisma/schema.prisma with all needed models.

When implementing a story, return ONLY valid JSON — no markdown fences, no explanation text, just raw JSON.

JSON structure:
{
  "summary": "1-2 sentence description of what was implemented",
  "new_packages": ["package-name"],
  "breaking_changes": [
    {
      "file": "path/to/file.ts",
      "description": "Changed API response shape from { subscriptions } to { data, total } — existing consumers must be updated"
    }
  ],
  "files": [
    {
      "path": "relative/path/from/project/root/file.tsx",
      "action": "create",
      "content": "full file content as a string"
    }
  ]
}

SCOPE RULES (critical — read carefully):
- Only touch files that are directly required by this story's acceptance criteria
- NEVER refactor, rename, or restructure existing files that are not part of this story
- NEVER change the response shape of an existing API endpoint unless the story explicitly requires it
- NEVER change existing component props or interfaces unless the story explicitly requires it
- NEVER change formatting, currency, or styling in components you are not building for this story
- If you need to call an existing API or use an existing component, work with its current interface — do not change it
- When in doubt: create a new file rather than modifying an existing one
- breaking_changes must list ANY change that modifies an existing contract (API response shape, component props, exported types). Leave as empty array [] if none.

API CONSISTENCY RULES (enforced — violations cause runtime crashes):
- Before writing ANY component that fetches data, look up the existing API route file shown in "Key existing files" and use EXACTLY the response shape it already returns.
- If the API route returns `{ subscriptions: [...] }` your component must use `json.subscriptions`. If it returns `{ data: [...], total: N }` use `json.data` and `json.total`. Never invent a new shape.
- If lib/types.ts defines `ApiSubscriptionsResponse`, your component must import and use that type — do not redefine it inline.
- If you must change an API response shape, you MUST update every existing consumer of that endpoint in the same PR AND list it as a breaking_change. If you cannot do that within the 3-4 file limit, do NOT change the shape — work with what exists.

General rules:
- Include the COMPLETE file content — never truncate or use placeholders like "// ... rest of file"
- Use proper TypeScript types everywhere
- Handle loading states, empty states, and error states in UI components
- Make the UI clean and functional with Tailwind
- new_packages is optional — only include if you need packages not already in a standard Next.js + Prisma + shadcn/ui setup

TESTING RULES (mandatory):
- Always include a Playwright e2e test file at e2e/{story-slug}.spec.ts
- The story slug is a kebab-case version of the story title (e.g. "add-subscription")
- Tests must cover the happy path and at least one error/edge case from the Acceptance Criteria
- Use { baseURL } from @playwright/test — the base URL is already configured in playwright.config.ts
- Add data-testid attributes to key interactive elements (buttons, forms, inputs) in your components so tests can find them reliably
- Keep tests simple: navigate → interact → assert. No complex setup needed.
- Example test structure:
  import { test, expect } from '@playwright/test';
  test('user can add a subscription', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('add-subscription-btn').click();
    await page.getByTestId('subscription-name-input').fill('Netflix');
    await page.getByTestId('save-btn').click();
    await expect(page.getByText('Netflix')).toBeVisible();
  });
"""

IMPLEMENT_PROMPT = """
Here is the user story specification to implement:

{spec}

---

Current project file tree:
{file_tree}

{key_files_section}

Implement this story completely. Return valid JSON only.
"""

FIX_ERRORS_PROMPT = """
The build failed with these errors after implementing a story. Fix them.

Build errors:
{errors}

Files that were written:
{files}

Return the corrected files as valid JSON using the same structure:
{{
  "summary": "what was fixed",
  "new_packages": [],
  "files": [{{ "path": "...", "action": "create", "content": "..." }}]
}}

Only include files that need to change. Return valid JSON only.
"""


class DeveloperAgent:
    def __init__(self, config: Config):
        self.client = Anthropic(api_key=config.anthropic_api_key, max_retries=5)
        self.model = config.claude_model
        self.project_path = Path(config.project_local_path)

    def _call(self, system: str, user: str) -> str:
        full_text = ""
        with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=32000,
            system=system,
            messages=[{"role": "user", "content": user}],
            betas=["output-128k-2025-02-19"],
        ) as stream:
            for text in stream.text_stream:
                full_text += text
        return full_text.strip()

    def _parse_json_response(self, raw: str) -> dict:
        """Strip markdown fences and parse JSON."""
        if not raw or not raw.strip():
            raise ValueError("Empty response from Claude — the input may be too large or the request timed out.")
        raw = re.sub(r"^```json\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"^```\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        return json.loads(raw.strip())

    def _get_file_tree(self) -> str:
        """Return a sorted list of project files, excluding noise folders."""
        exclude = {".git", "node_modules", ".next", "__pycache__", ".cache"}
        files = []
        if self.project_path.exists():
            for root, dirs, filenames in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in exclude]
                for filename in filenames:
                    rel = os.path.relpath(os.path.join(root, filename), self.project_path)
                    files.append(rel)
        return "\n".join(sorted(files)) if files else "(empty — project not scaffolded yet)"

    def _read_key_files(self) -> str:
        """Read important existing files so the agent understands the current codebase."""
        key_files = [
            "package.json",
            "prisma/schema.prisma",
            "lib/prisma.ts",
            "lib/types.ts",
            "app/layout.tsx",
            "app/page.tsx",
        ]
        sections = []
        for f in key_files:
            path = self.project_path / f
            if path.exists():
                sections.append(f"=== {f} ===\n{path.read_text()}")

        # Also read all existing API routes so the agent knows exact response shapes
        api_dir = self.project_path / "app" / "api"
        if api_dir.exists():
            for route_file in sorted(api_dir.rglob("route.ts")):
                rel = route_file.relative_to(self.project_path)
                sections.append(f"=== {rel} ===\n{route_file.read_text()}")

        return "\n\n".join(sections)

    def check_node(self):
        """Verify Node.js is installed. Raises RuntimeError if not."""
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                "Node.js is not installed or not in PATH.\n"
                "Download it from https://nodejs.org (choose the LTS version)."
            )

    def scaffold_if_needed(self, console=None) -> bool:
        """
        Scaffold a new Next.js project if package.json doesn't exist.
        Returns True if scaffolding happened.
        """
        if (self.project_path / "package.json").exists():
            return False

        self.project_path.mkdir(parents=True, exist_ok=True)

        def run(cmd, description):
            if console:
                console.print(f"  [dim]{description}...[/dim]")
            result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")

        # Scaffold Next.js with TypeScript, Tailwind, App Router
        run(
            ["npx", "create-next-app@latest", ".",
             "--typescript", "--tailwind", "--app",
             "--no-src-dir", "--no-import-alias", "--yes"],
            "Creating Next.js project (this takes a minute)",
        )

        # Install Prisma (no native compilation needed)
        run(
            ["npm", "install", "prisma", "@prisma/client"],
            "Installing Prisma",
        )

        # Install shadcn/ui
        run(
            ["npx", "shadcn@latest", "init", "--yes", "--defaults"],
            "Setting up shadcn/ui",
        )

        return True

    def implement_story(self, spec: str) -> dict:
        """Generate the implementation for a story. Returns parsed JSON."""
        file_tree = self._get_file_tree()
        key_files = self._read_key_files()

        key_files_section = (
            f"Key existing files for context:\n\n{key_files}"
            if key_files
            else ""
        )

        prompt = IMPLEMENT_PROMPT.format(
            spec=spec,
            file_tree=file_tree,
            key_files_section=key_files_section,
        )

        raw = self._call(DEVELOPER_SYSTEM_PROMPT, prompt)
        return self._parse_json_response(raw)

    def apply_files(self, implementation: dict):
        """Write all generated files to disk."""
        for file in implementation.get("files", []):
            path = self.project_path / file["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file["content"], encoding="utf-8")

    def install_packages(self, packages: list[str]):
        """Install any new npm packages the agent requested."""
        if not packages:
            return
        subprocess.run(
            ["npm", "install"] + packages,
            cwd=self.project_path,
            check=True,
        )

    def setup_playwright(self, console=None) -> bool:
        """Install Playwright and create config if not already set up. Returns True if newly set up."""
        config_path = self.project_path / "playwright.config.ts"
        if config_path.exists():
            return False

        if console:
            console.print("  [dim]Installing Playwright...[/dim]")

        subprocess.run(
            ["npm", "install", "--save-dev", "@playwright/test"],
            cwd=self.project_path, check=True, capture_output=True,
        )
        subprocess.run(
            ["npx", "playwright", "install", "chromium"],
            cwd=self.project_path, check=True, capture_output=True,
        )

        # Create playwright.config.ts
        config_path.write_text(
            'import { defineConfig } from \'@playwright/test\';\n\n'
            'export default defineConfig({\n'
            '  testDir: \'./e2e\',\n'
            '  timeout: 30000,\n'
            '  use: {\n'
            '    baseURL: \'http://localhost:3000\',\n'
            '    headless: true,\n'
            '  },\n'
            '  webServer: {\n'
            '    command: \'npm run dev\',\n'
            '    url: \'http://localhost:3000\',\n'
            '    reuseExistingServer: true,\n'
            '    timeout: 120000,\n'
            '  },\n'
            '});\n',
            encoding="utf-8",
        )

        # Create e2e directory
        (self.project_path / "e2e").mkdir(exist_ok=True)

        if console:
            console.print("  [green]✓[/green] Playwright configured")
        return True

    def run_e2e_tests(self) -> tuple[bool, str]:
        """Run Playwright e2e tests. Returns (passed, output)."""
        e2e_dir = self.project_path / "e2e"
        if not e2e_dir.exists() or not list(e2e_dir.glob("*.spec.ts")):
            return True, "No e2e tests found — skipping."
        result = subprocess.run(
            ["npx", "playwright", "test", "--reporter=line"],
            cwd=self.project_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0, result.stdout + result.stderr

    def build_check(self) -> tuple[bool, str]:
        """Run `npm run build`. Returns (success, output)."""
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=self.project_path,
            capture_output=True,
            text=True,
            timeout=180,
        )
        return result.returncode == 0, result.stdout + result.stderr

    def fix_build_errors(self, errors: str, previous_implementation: dict) -> dict:
        """Ask the agent to fix TypeScript/build errors."""
        # Keep only the last 4000 chars of build output (errors are at the end)
        errors_truncated = errors[-4000:] if len(errors) > 4000 else errors
        # Send full content only for files mentioned in the errors, others path-only
        error_text = errors_truncated.lower()
        files = previous_implementation.get("files", [])
        relevant_files = []
        for f in files:
            path = f.get("path", "")
            filename = path.split("/")[-1].lower()
            if filename in error_text or path.lower() in error_text:
                relevant_files.append({"path": path, "content": f.get("content", "")})
            else:
                relevant_files.append({"path": path, "content": "(unchanged)"})
        prompt = FIX_ERRORS_PROMPT.format(
            errors=errors_truncated,
            files=json.dumps(relevant_files, indent=2),
        )
        raw = self._call(DEVELOPER_SYSTEM_PROMPT, prompt)
        return self._parse_json_response(raw)
