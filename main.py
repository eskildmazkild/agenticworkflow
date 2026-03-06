#!/usr/bin/env python3
"""
Spec Agent — Agentic development workflow tool

Commands:
    python3 main.py              → Start a new epic (Phase 1)
    python3 main.py dev-start    → Pick a story and develop it (Phase 2)
    python3 main.py review-pr    → Review a PR and merge if approved (Phase 3)
    python3 main.py restart      → Kill and restart the Next.js dev server
"""
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
import typer

from config import Config
from agents.epic_agent import EpicAgent
from agents.story_agent import StoryAgent
from agents.review_agent import ReviewAgent
from agents.developer_agent import DeveloperAgent
from github_client import GitHubClient
from ui import (
    console,
    get_epic_input,
    print_error,
    print_step,
    print_success,
    print_warning,
    review_loop,
)

app = typer.Typer(
    help="Spec Agent — spec-driven development workflow tool",
    add_completion=False,
    invoke_without_command=True,
)


# ══════════════════════════════════════════════════════════════
# PHASE 1: New Epic
# ══════════════════════════════════════════════════════════════

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Run with no arguments to start a new epic (Phase 1)."""
    if ctx.invoked_subcommand is None:
        new_epic()


def new_epic():
    console.print(
        Panel(
            "[bold]Spec Agent — Phase 1: Spec Machine[/bold]\n\n"
            "Flow:\n"
            "  1. You provide a brief epic outline\n"
            "  2. Agent expands it into a full epic specification  ← [yellow]you review[/yellow]\n"
            "  3. Agent writes specs for each user story           ← [yellow]you review each[/yellow]\n"
            "  4. Everything is pushed to GitHub as Issues + spec files",
            title="[bold blue]🤖 Spec Agent[/bold blue]",
            border_style="blue",
        )
    )

    try:
        config = Config.load()
    except EnvironmentError as e:
        print_error(str(e))
        sys.exit(1)

    title, outline = get_epic_input(console)
    if not title.strip() or not outline.strip():
        print_error("Epic title and outline are required.")
        sys.exit(1)

    print_step(f"Expanding epic: '{title}'")
    epic_agent = EpicAgent(config)

    with console.status("[bold green]Agent is writing the epic specification...[/bold green]"):
        epic_doc = epic_agent.expand_epic(title, outline)

    console.print("\n[bold yellow]━━━ REVIEW POINT 1: Epic Specification ━━━[/bold yellow]")
    epic_doc = review_loop(
        content=epic_doc,
        title="Epic Specification",
        revise_fn=lambda feedback: epic_agent.revise_epic(epic_doc, feedback),
        console=console,
    )

    print_step("Extracting user stories from approved epic...")
    story_titles = epic_agent.extract_story_titles(epic_doc)

    if not story_titles:
        print_warning("Could not extract story titles. Check the 'User Stories' section.")
        sys.exit(1)

    console.print(f"\n[bold]Found [green]{len(story_titles)}[/green] user stories:[/bold]")
    for i, t in enumerate(story_titles, 1):
        console.print(f"  {i}. {t}")

    if not Confirm.ask("\n[bold]Continue to write specs for all stories?[/bold]", default=True):
        print_warning("Aborted.")
        sys.exit(0)

    story_agent = StoryAgent(config)
    approved_stories = []

    for i, story_title in enumerate(story_titles, 1):
        console.print(f"\n[bold yellow]━━━ REVIEW POINT 2.{i}: Story {i}/{len(story_titles)} ━━━[/bold yellow]")
        print_step(f"Writing spec for: {story_title}")

        with console.status("[bold green]Agent is writing story spec...[/bold green]"):
            story_doc = story_agent.write_story(epic_context=epic_doc, story_title=story_title)

        current_story_doc = story_doc
        story_doc = review_loop(
            content=current_story_doc,
            title=f"Story Spec: {story_title}",
            revise_fn=lambda feedback, doc=current_story_doc: story_agent.revise_story(doc, feedback),
            console=console,
        )

        approved_stories.append({"title": story_title, "content": story_doc})
        print_success(f"Story {i}/{len(story_titles)} approved: {story_title}")

    console.print(f"\n[bold yellow]━━━ FINAL STEP: Push to GitHub ━━━[/bold yellow]")
    if not Confirm.ask("\n[bold green]Push everything to GitHub?[/bold green]", default=True):
        print_warning("Aborted. Nothing was pushed.")
        sys.exit(0)

    github = GitHubClient(config)
    try:
        with console.status("[bold green]Creating epic issue...[/bold green]"):
            created_epic = github.create_epic_issue(title, epic_doc)
        console.print(f"  [green]✓[/green] Epic #{created_epic.issue_number} — {created_epic.issue_url}")

        for story in approved_stories:
            with console.status(f"[bold green]Creating story issue: {story['title']}[/bold green]"):
                created_story = github.create_story_issue(
                    title=story["title"],
                    story_markdown=story["content"],
                    epic_issue_number=created_epic.issue_number,
                )
            story["issue_number"] = created_story.issue_number
            console.print(f"  [green]✓[/green] Story #{created_story.issue_number} — {story['title']}")

        with console.status("[bold green]Committing spec files...[/bold green]"):
            github.create_spec_files(
                epic_title=title,
                epic_markdown=epic_doc,
                stories=approved_stories,
                epic_issue_number=created_epic.issue_number,
            )
        console.print(f"  [green]✓[/green] Spec files committed to: {config.specs_folder}/epic-{created_epic.issue_number}-{created_epic.slug}/")

    except Exception as e:
        print_error(f"GitHub error: {e}")
        sys.exit(1)

    console.print(Panel(
        f"[bold green]Epic created![/bold green]\n\n"
        f"Epic:    {created_epic.issue_url}\n"
        f"Stories: {len(approved_stories)} issues\n\n"
        f"[italic]Run [bold]python3 main.py dev-start[/bold] to begin development.[/italic]",
        title="[bold blue]✅ Done[/bold blue]",
        border_style="green",
    ))


# ══════════════════════════════════════════════════════════════
# PHASE 2: Developer Agent
# ══════════════════════════════════════════════════════════════

@app.command("dev-start")
def dev_start():
    """Pick an approved story and let the developer agent implement it."""
    console.print(Panel(
        "[bold]Spec Agent — Phase 2: Developer Agent[/bold]\n\n"
        "Flow:\n"
        "  1. Pick a story from your approved backlog\n"
        "  2. Agent scaffolds the project (first time only)\n"
        "  3. Agent reads the spec and writes the code\n"
        "  4. Build is verified automatically\n"
        "  5. Branch is pushed and a PR is created on GitHub\n"
        "  6. GitHub Issue moves to [yellow]in-review[/yellow]",
        title="[bold blue]👨‍💻 Developer Agent[/bold blue]",
        border_style="blue",
    ))

    # ── Load config ────────────────────────────────────────────
    try:
        config = Config.load()
    except EnvironmentError as e:
        print_error(str(e))
        sys.exit(1)

    if not config.project_local_path:
        print_error(
            "PROJECT_LOCAL_PATH is not set in your .env file.\n"
            "Add the path to your local project folder, e.g.:\n"
            "  PROJECT_LOCAL_PATH=/Users/eskildmadseskildsen/coding/subscription-tool"
        )
        sys.exit(1)

    project_path = Path(config.project_local_path)
    github = GitHubClient(config)
    agent = DeveloperAgent(config)

    # ── Check Node.js is installed ─────────────────────────────
    try:
        agent.check_node()
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(1)

    # ── List ready stories ─────────────────────────────────────
    print_step("Fetching approved stories from GitHub...")
    with console.status("[bold green]Loading backlog...[/bold green]"):
        stories = github.list_ready_stories()

    if not stories:
        print_warning("No approved stories found in the backlog.")
        console.print("[italic]Stories need the labels 'user-story' and 'spec-approved' to appear here.[/italic]")
        sys.exit(0)

    console.print(f"\n[bold]Approved stories ready for development:[/bold]\n")
    for i, s in enumerate(stories, 1):
        console.print(f"  [bold]{i}.[/bold] #{s.issue_number} — {s.title}")

    choice = Prompt.ask(
        "\n[bold blue]Which story do you want to develop?[/bold blue] (enter number)",
        default="1",
    )
    try:
        selected = stories[int(choice) - 1]
    except (ValueError, IndexError):
        print_error("Invalid choice.")
        sys.exit(1)

    console.print(f"\n[bold green]Selected:[/bold green] #{selected.issue_number} — {selected.title}")
    console.print(f"[dim]{selected.url}[/dim]\n")

    # ── Mark in-progress on GitHub ─────────────────────────────
    print_step("Marking story as in-progress on GitHub...")
    github.mark_in_progress(selected.issue_number)

    # ── Everything from here is wrapped — on ANY failure, reset labels ──
    try:
        # ── Read spec ───────────────────────────────────────────
        print_step("Reading spec from GitHub...")
        spec = github.get_spec_content(
            epic_number=selected.epic_number,
            story_slug=selected.slug,
        )

        if not spec:
            print_warning("Could not find spec file in GitHub. Check that specs were committed in Phase 1.")
            sys.exit(1)

        console.print(f"  [green]✓[/green] Spec loaded ({len(spec)} characters)")

        # ── Ensure project repo is cloned locally ───────────────
        if not project_path.exists():
            if Confirm.ask(
                f"\n[yellow]Project folder not found at {project_path}. Clone it from GitHub now?[/yellow]",
                default=True,
            ):
                print_step(f"Cloning {config.github_repo}...")
                subprocess.run(
                    ["git", "clone", f"https://github.com/{config.github_repo}.git", str(project_path)],
                    check=True,
                )
            else:
                print_error("Cannot continue without a local project folder.")
                sys.exit(1)

        # ── Git: sync + create feature branch ───────────────────
        branch = f"feature/{selected.slug}-{selected.issue_number}"
        print_step(f"Creating branch: {branch}")

        subprocess.run(["git", "fetch", "origin"], cwd=project_path)
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=project_path)
        subprocess.run(["git", "checkout", "-B", branch], cwd=project_path, check=True)

        # ── Scaffold Next.js if first time ──────────────────────
        with console.status("[bold green]Checking project setup...[/bold green]"):
            scaffolded = agent.scaffold_if_needed(console=console)

        if scaffolded:
            print_success("Next.js project scaffolded successfully!")
            subprocess.run(["git", "add", "-A"], cwd=project_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "chore: scaffold Next.js project with Tailwind + shadcn/ui + SQLite"],
                cwd=project_path, check=True,
            )

        # ── Set up Playwright if first time ─────────────────────
        with console.status("[bold green]Checking Playwright setup...[/bold green]"):
            pw_new = agent.setup_playwright(console=console)
        if pw_new:
            subprocess.run(["git", "add", "-A"], cwd=project_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "chore: add Playwright e2e test setup"],
                cwd=project_path, check=True,
            )

        # ── Generate code ────────────────────────────────────────
        print_step("Agent is implementing the story...")
        with console.status("[bold green]Generating code (this may take a moment)...[/bold green]"):
            implementation = agent.implement_story(spec)

        console.print(f"\n  [green]✓[/green] Implementation plan: {implementation.get('summary', '')}")
        console.print(f"  [green]✓[/green] Files to write: {len(implementation.get('files', []))}")

        # ── Breaking changes gate ─────────────────────────────────
        breaking = implementation.get("breaking_changes", [])
        if breaking:
            console.print(f"\n[bold red]⚠️  Agent wants to make {len(breaking)} BREAKING CHANGE(S):[/bold red]\n")
            for bc in breaking:
                console.print(f"  [red]•[/red] [bold]{bc.get('file', '')}[/bold]")
                console.print(f"    {bc.get('description', '')}\n")
            console.print("[italic]Breaking changes modify existing APIs or component contracts and may break other parts of the app.[/italic]")
            approve = Confirm.ask(
                "\n[bold yellow]Do you want to allow these breaking changes?[/bold yellow]",
                default=False,
            )
            if not approve:
                print_warning("Breaking changes rejected — resetting labels.")
                raise KeyboardInterrupt("Breaking changes not approved by user.")

        # ── Write files ──────────────────────────────────────────
        print_step("Writing files to project...")
        agent.apply_files(implementation)

        if implementation.get("new_packages"):
            console.print(f"  Installing packages: {', '.join(implementation['new_packages'])}")
            agent.install_packages(implementation["new_packages"])

        for f in implementation.get("files", []):
            console.print(f"  [green]✓[/green] {f['action']}: {f['path']}")

        # ── Prisma db push (if schema changed) ───────────────────
        changed_paths = [f["path"] for f in implementation.get("files", [])]
        if any("schema.prisma" in p for p in changed_paths):
            print_step("Pushing Prisma schema to database...")
            result = subprocess.run(
                ["npx", "prisma", "db", "push"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                console.print("  [green]✓[/green] Database schema updated")
            else:
                print_warning(f"prisma db push failed:\n{result.stdout + result.stderr}")

        # ── Build check (up to 3 attempts) ───────────────────────
        print_step("Running build check...")
        last_implementation = implementation
        build_ok = False

        for attempt in range(1, 4):
            with console.status(f"[bold green]Building... (attempt {attempt}/3)[/bold green]"):
                build_ok, output = agent.build_check()

            if build_ok:
                print_success("Build passed!")
                break
            else:
                console.print(f"  [yellow]⚠ Build failed on attempt {attempt}[/yellow]")
                if attempt < 3:
                    console.print("  [italic]Agent is fixing errors...[/italic]")
                    try:
                        with console.status("[bold green]Fixing build errors...[/bold green]"):
                            fix = agent.fix_build_errors(output, last_implementation)
                        agent.apply_files(fix)
                        last_implementation = fix
                    except Exception as fix_err:
                        print_warning(f"Fix attempt {attempt} failed ({fix_err}) — retrying build as-is")
                else:
                    print_warning("Build still failing after 3 attempts.")
                    console.print("[italic]You may want to fix the remaining errors manually before merging the PR.[/italic]")

        # ── E2E tests ─────────────────────────────────────────────
        print_step("Running Playwright e2e tests...")
        with console.status("[bold green]Running e2e tests (dev server must be running)...[/bold green]"):
            tests_ok, test_output = agent.run_e2e_tests()

        if tests_ok:
            print_success("E2e tests passed!")
        else:
            print_warning("E2e tests failed — review before merging.")
            # Show last 20 lines of test output
            lines = test_output.strip().splitlines()
            for line in lines[-20:]:
                console.print(f"  [dim]{line}[/dim]")

        # ── Git: commit + push ────────────────────────────────────
        print_step("Committing and pushing to GitHub...")
        subprocess.run(["git", "add", "-A"], cwd=project_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: implement story #{selected.issue_number} - {selected.title}"],
            cwd=project_path, check=True,
        )
        subprocess.run(
            ["git", "push", "--set-upstream", "origin", branch],
            cwd=project_path, check=True,
        )
        console.print(f"  [green]✓[/green] Pushed branch: {branch}")

        # ── Create PR ─────────────────────────────────────────────
        print_step("Creating Pull Request...")
        test_badge = "✅ passing" if tests_ok else "⚠️ failing — review before merging"
        pr_body = (
            f"## Summary\n{implementation.get('summary', '')}\n\n"
            f"## Closes\nCloses #{selected.issue_number}\n\n"
            f"## E2e tests\n{test_badge}\n\n"
            f"## Files changed\n"
            + "\n".join(f"- `{f['path']}`" for f in implementation.get("files", []))
            + "\n\n---\n🤖 Implemented by Developer Agent"
        )

        try:
            pr_url = github.create_pull_request(
                title=f"feat: {selected.title} (#{selected.issue_number})",
                body=pr_body,
                branch=branch,
            )
            console.print(f"  [green]✓[/green] PR created: {pr_url}")
        except Exception as e:
            print_warning(f"Could not create PR automatically: {e}")
            print_warning("Create the PR manually on GitHub.")
            pr_url = f"https://github.com/{config.github_repo}/compare/{branch}"

        # ── Move issue to in-review ───────────────────────────────
        github.mark_in_review(selected.issue_number, pr_url, branch)
        console.print(f"  [green]✓[/green] Issue #{selected.issue_number} moved to in-review")

    except (Exception, KeyboardInterrupt) as e:
        # ── Reset labels on any failure or Ctrl+C ─────────────────
        console.print(f"\n[bold red]✗ Something went wrong — resetting labels on #{selected.issue_number}[/bold red]")
        try:
            issue = github.repo.get_issue(selected.issue_number)
            issue.add_to_labels("spec-approved")
            try:
                issue.remove_from_labels("in-progress")
            except Exception:
                pass
            console.print(f"  [green]✓[/green] Issue #{selected.issue_number} reset to spec-approved")
        except Exception:
            print_warning(f"Could not reset labels — do it manually on GitHub for issue #{selected.issue_number}")
        if not isinstance(e, KeyboardInterrupt):
            raise

    # ── Done ─────────────────────────────────────────────────
    console.print(Panel(
        f"[bold green]Story implemented![/bold green]\n\n"
        f"Story:   #{selected.issue_number} — {selected.title}\n"
        f"Branch:  {branch}\n"
        f"PR:      {pr_url}\n"
        f"Build:   {'✅ passing' if build_ok else '⚠️  failing — needs manual fix'}\n\n"
        f"[italic]Review the PR, then merge to deploy.[/italic]",
        title="[bold blue]✅ Done[/bold blue]",
        border_style="green",
    ))


# ══════════════════════════════════════════════════════════════
# PHASE 3: Review Agent
# ══════════════════════════════════════════════════════════════

@app.command("review-pr")
def review_pr():
    """Review an open PR with the AI agent and merge if approved (Phase 3)."""
    console.print(Panel(
        "[bold]Spec Agent — Phase 3: Review Agent[/bold]\n\n"
        "Flow:\n"
        "  1. Pick a story from your in-review backlog\n"
        "  2. Agent reads the spec and the PR diff\n"
        "  3. Agent evaluates each acceptance criterion\n"
        "  4. You see a structured verdict                ← [yellow]you decide[/yellow]\n"
        "  5. Approve → PR is merged, issue closed, PO emailed\n"
        "  6. Request changes → story sent back to in-progress",
        title="[bold blue]🔍 Review Agent[/bold blue]",
        border_style="blue",
    ))

    # ── Load config ────────────────────────────────────────────
    try:
        config = Config.load()
    except EnvironmentError as e:
        print_error(str(e))
        sys.exit(1)

    github = GitHubClient(config)
    agent = ReviewAgent(config)

    # ── List in-review stories ─────────────────────────────────
    print_step("Fetching in-review stories from GitHub...")
    with console.status("[bold green]Loading stories...[/bold green]"):
        stories = github.list_in_review_stories()

    if not stories:
        print_warning("No stories currently in review.")
        console.print("[italic]Stories need the labels 'user-story' and 'in-review' to appear here.[/italic]")
        sys.exit(0)

    console.print(f"\n[bold]Stories awaiting review:[/bold]\n")
    for i, s in enumerate(stories, 1):
        console.print(f"  [bold]{i}.[/bold] #{s.issue_number} — {s.title}")

    choice = Prompt.ask(
        "\n[bold blue]Which story do you want to review?[/bold blue] (enter number)",
        default="1",
    )
    try:
        selected = stories[int(choice) - 1]
    except (ValueError, IndexError):
        print_error("Invalid choice.")
        sys.exit(1)

    console.print(f"\n[bold green]Selected:[/bold green] #{selected.issue_number} — {selected.title}")

    # ── Find PR ────────────────────────────────────────────────
    print_step("Finding the open PR for this story...")
    with console.status("[bold green]Searching for PR...[/bold green]"):
        pr = github.get_pr_for_issue(selected.issue_number)

    if not pr:
        print_error(
            f"Could not find an open PR linked to issue #{selected.issue_number}.\n"
            "Make sure the PR body contains 'Closes #{selected.issue_number}'."
        )
        sys.exit(1)

    console.print(f"  [green]✓[/green] Found PR #{pr.number}: {pr.title}")
    console.print(f"  [dim]{pr.html_url}[/dim]")

    # ── Load spec + diff ───────────────────────────────────────
    print_step("Loading spec and PR diff...")
    with console.status("[bold green]Fetching data...[/bold green]"):
        spec = github.get_spec_content(
            epic_number=selected.epic_number,
            story_slug=selected.slug,
        )
        diff = github.get_pr_diff(pr.number)

    if not spec:
        print_warning("Could not find spec file. Continuing with PR diff only.")
        spec = f"User story: {selected.title}\n\n(Spec file not found in repo)"

    console.print(f"  [green]✓[/green] Spec: {len(spec)} characters")
    console.print(f"  [green]✓[/green] Diff: {len(diff)} characters")

    # ── AI Review ──────────────────────────────────────────────
    print_step("Agent is reviewing the PR...")
    with console.status("[bold green]Analysing spec vs diff (this may take a moment)...[/bold green]"):
        review = agent.review_pr(spec, diff)

    # ── Display results ────────────────────────────────────────
    verdict = review.get("verdict", "request_changes")
    verdict_color = "green" if verdict == "approved" else "yellow"
    verdict_label = "✅ APPROVED" if verdict == "approved" else "⚠️  REQUEST CHANGES"

    console.print(f"\n[bold {verdict_color}]━━━ AGENT VERDICT: {verdict_label} ━━━[/bold {verdict_color}]")
    console.print(f"\n[bold]Summary:[/bold] {review.get('summary', '')}\n")

    # AC table
    ac_items = review.get("ac_review", [])
    if ac_items:
        table = Table(title="Acceptance Criteria Review", show_lines=True)
        table.add_column("Criterion", style="bold", min_width=20)
        table.add_column("Status", min_width=12)
        table.add_column("Comment")

        status_colors = {
            "implemented": "[green]✅ implemented[/green]",
            "partial":     "[yellow]⚠️  partial[/yellow]",
            "missing":     "[red]❌ missing[/red]",
        }
        for ac in ac_items:
            status_raw = ac.get("status", "")
            table.add_row(
                ac.get("criterion", ""),
                status_colors.get(status_raw, status_raw),
                ac.get("comment", ""),
            )
        console.print(table)

    # Issues
    issues = review.get("issues", [])
    if issues:
        console.print("\n[bold red]Issues that must be fixed:[/bold red]")
        for issue in issues:
            console.print(f"  • {issue}")

    # Strengths
    strengths = review.get("strengths", [])
    if strengths:
        console.print("\n[bold green]Strengths:[/bold green]")
        for s in strengths:
            console.print(f"  • {s}")

    # ── Human decision ─────────────────────────────────────────
    console.print(f"\n[bold yellow]━━━ YOUR DECISION ━━━[/bold yellow]")
    console.print(f"Agent recommends: [bold {verdict_color}]{verdict_label}[/bold {verdict_color}]")
    console.print("\n  [bold]1.[/bold] Approve and merge (agent approved or override)")
    console.print("  [bold]2.[/bold] Request changes (send back to developer)")
    console.print("  [bold]3.[/bold] Skip — do nothing now")

    decision = Prompt.ask(
        "\n[bold blue]Your decision[/bold blue]",
        choices=["1", "2", "3"],
        default="1" if verdict == "approved" else "2",
    )

    # ── Execute decision ───────────────────────────────────────
    if decision == "1":
        # Approve + merge
        print_step("Posting approval and merging PR...")
        review_body = (
            f"## AI Review: {verdict_label}\n\n"
            f"{review.get('summary', '')}\n\n"
            "### Acceptance Criteria\n"
            + "\n".join(
                f"- **{ac.get('criterion')}**: {ac.get('status')} — {ac.get('comment')}"
                for ac in ac_items
            )
            + "\n\n---\n🤖 Reviewed by Review Agent"
        )

        try:
            github.post_pr_review(pr.number, review_body, approve=True)
            console.print(f"  [green]✓[/green] Review posted")
        except Exception as e:
            print_warning(f"Could not post review: {e}")

        try:
            commit_msg = f"feat: {selected.title} (#{selected.issue_number})"
            github.merge_pr(pr.number, commit_msg)
            console.print(f"  [green]✓[/green] PR #{pr.number} merged")
        except Exception as e:
            print_error(f"Could not merge PR: {e}")
            sys.exit(1)

        github.mark_done(selected.issue_number)
        console.print(f"  [green]✓[/green] Issue #{selected.issue_number} closed and marked done")

        # Send PO email
        print_step("Sending PO summary email...")
        sent = agent.send_email_summary(selected.title, review)
        if sent:
            print_success(f"Email sent to {config.po_email}")
        else:
            print_warning("Email not sent (check PO_EMAIL / GMAIL_SENDER / GMAIL_APP_PASSWORD in .env)")

        console.print(Panel(
            f"[bold green]Story shipped![/bold green]\n\n"
            f"Story:  #{selected.issue_number} — {selected.title}\n"
            f"PR:     #{pr.number} merged ✅\n"
            f"Email:  {'sent ✅' if sent else 'skipped ⚠️'}\n\n"
            f"[italic]Run [bold]python3 main.py dev-start[/bold] to pick the next story.[/italic]",
            title="[bold blue]✅ Done[/bold blue]",
            border_style="green",
        ))

    elif decision == "2":
        # Request changes
        print_step("Posting review requesting changes...")
        review_body = (
            f"## AI Review: ⚠️ REQUEST CHANGES\n\n"
            f"{review.get('summary', '')}\n\n"
            "### Issues to fix\n"
            + "\n".join(f"- {i}" for i in issues)
            + "\n\n### Acceptance Criteria\n"
            + "\n".join(
                f"- **{ac.get('criterion')}**: {ac.get('status')} — {ac.get('comment')}"
                for ac in ac_items
            )
            + "\n\n---\n🤖 Reviewed by Review Agent"
        )

        try:
            github.post_pr_review(pr.number, review_body, approve=False)
            console.print(f"  [green]✓[/green] Review posted (changes requested)")
        except Exception as e:
            print_warning(f"Could not post review: {e}")

        github.reopen_for_changes(selected.issue_number)
        console.print(f"  [green]✓[/green] Issue #{selected.issue_number} moved back to in-progress")

        console.print(Panel(
            f"[bold yellow]Changes requested.[/bold yellow]\n\n"
            f"Story:  #{selected.issue_number} — {selected.title}\n"
            f"PR:     #{pr.number} (open, changes requested)\n\n"
            f"[italic]Run [bold]python3 main.py dev-start[/bold] to pick it up again.[/italic]",
            title="[bold yellow]↩ Back to Development[/bold yellow]",
            border_style="yellow",
        ))

    else:
        print_warning("Skipped — no changes made.")


@app.command("restart")
def restart_server():
    """Kill the Next.js dev server on port 3000 and start it again."""
    try:
        config = Config.load()
        project_path = Path(config.project_local_path)
    except Exception:
        print_error("Could not load config — check your .env file.")
        sys.exit(1)

    # Kill whatever is on port 3000
    result = subprocess.run(
        ["lsof", "-ti:3000"],
        capture_output=True, text=True,
    )
    pids = result.stdout.strip()
    if pids:
        subprocess.run(["kill"] + pids.split(), capture_output=True)
        console.print("  [green]✓[/green] Stopped server on port 3000")
    else:
        console.print("  [dim]No server running on port 3000[/dim]")

    # Start dev server in background
    console.print("  [dim]Starting dev server...[/dim]")
    subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=project_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print_success("Dev server restarted — open http://localhost:3000")


@app.command("kill")
def kill_servers():
    """Kill all processes running on common dev ports (3000-3010)."""
    killed = []
    for port in range(3000, 3011):
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True,
        )
        pids = result.stdout.strip()
        if pids:
            subprocess.run(["kill"] + pids.split(), capture_output=True)
            killed.append(port)

    if killed:
        print_success(f"Killed servers on port(s): {', '.join(str(p) for p in killed)}")
    else:
        console.print("  [dim]No servers running on ports 3000–3010[/dim]")


if __name__ == "__main__":
    app()
