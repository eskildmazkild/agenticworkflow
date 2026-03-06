"""
Terminal UI helpers for spec-agent using Rich.
Handles the human-in-the-loop review loops.
"""
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.text import Text


console = Console()


def display_document(content: str, title: str):
    """Render a markdown document in a styled panel."""
    console.print()
    console.print(Rule(f"[bold blue]{title}[/bold blue]"))
    console.print(Markdown(content))
    console.print(Rule())
    console.print()


def review_loop(
    content: str,
    title: str,
    revise_fn,
    console: Console = console,
) -> str:
    """
    Show a document to the human reviewer and loop until approved.

    Args:
        content: The markdown content to review
        title: Display title for the review panel
        revise_fn: Callable(feedback: str) -> str that returns revised content
        console: Rich Console instance

    Returns:
        The approved content (possibly revised multiple times)
    """
    current = content
    revision = 0

    while True:
        display_document(current, title + (f" (revision {revision})" if revision > 0 else ""))

        console.print(
            Panel(
                "[bold]Review options:[/bold]\n"
                "  [green]y[/green] / [green]yes[/green]  → Approve and continue\n"
                "  [yellow]f[/yellow] / [yellow]feedback[/yellow] → Provide feedback for revision\n"
                "  [cyan]s[/cyan] / [cyan]skip[/cyan]    → Skip this item (use as-is)",
                title="[bold]Your review[/bold]",
                border_style="blue",
                expand=False,
            )
        )

        choice = Prompt.ask(
            "[bold blue]Action[/bold blue]",
            choices=["y", "yes", "f", "feedback", "s", "skip"],
            default="y",
        ).lower()

        if choice in ("y", "yes"):
            console.print("[bold green]✓ Approved[/bold green]")
            return current

        elif choice in ("s", "skip"):
            console.print("[yellow]⚠ Skipped — using current version[/yellow]")
            return current

        elif choice in ("f", "feedback"):
            feedback = _get_multiline_input(
                console,
                prompt="Enter your feedback (press Enter twice when done):",
            )
            if not feedback.strip():
                console.print("[yellow]No feedback entered. Please try again.[/yellow]")
                continue

            revision += 1
            console.print(f"\n[bold blue]Revising... (revision {revision})[/bold blue]")
            with console.status("[bold green]Agent is revising...[/bold green]"):
                current = revise_fn(feedback)


def _get_multiline_input(console: Console, prompt: str) -> str:
    """
    Get multi-line text input from the user.
    User presses Enter twice (blank line) to finish.
    """
    console.print(f"\n[italic]{prompt}[/italic]")
    lines = []
    consecutive_empty = 0

    while consecutive_empty < 1:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            consecutive_empty += 1
        else:
            consecutive_empty = 0
            lines.append(line)

    return "\n".join(lines)


def get_epic_input(console: Console) -> tuple[str, str]:
    """
    Prompt the PO for an epic title and outline.
    Returns (title, outline).
    """
    console.print(
        Panel(
            "[bold]You are starting a new epic.[/bold]\n\n"
            "Describe your epic briefly — the agent will expand it into a full specification.\n"
            "Don't worry about format or detail level. Even a few sentences is enough.",
            title="[bold blue]📋 New Epic[/bold blue]",
            border_style="blue",
        )
    )

    title = Prompt.ask("[bold]Epic title[/bold]")
    console.print(
        "\n[italic]Enter your epic outline (press Enter twice when done):[/italic]"
    )
    outline = _get_multiline_input(console, "")
    return title, outline


def print_success(message: str):
    console.print(f"\n[bold green]✅ {message}[/bold green]\n")


def print_step(message: str):
    console.print(f"\n[bold blue]→ {message}[/bold blue]")


def print_warning(message: str):
    console.print(f"\n[yellow]⚠ {message}[/yellow]")


def print_error(message: str):
    console.print(f"\n[bold red]✗ {message}[/bold red]")
