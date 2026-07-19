"""Rich-based UI helpers for Pokkie."""
from __future__ import annotations
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.align import Align
from rich.padding import Padding
from rich import box

console = Console()

BRAND = "pokkie"
ACCENT = "bold #a78bfa"
MUTED = "dim #94a3b8"
USER = "bold #22d3ee"
AI = "bold #f472b6"
OK = "bold #10b981"
WARN = "bold #fbbf24"
BAD = "bold #ef4444"


def banner(model: str, has_key: bool) -> None:
    logo = Text()
    if console.width >= 78:
        logo.append("██████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗███████╗\n", style=ACCENT)
        logo.append("██╔══██╗██╔═══██╗██║ ██╔╝██║ ██╔╝██║██╔════╝\n", style=ACCENT)
        logo.append("██████╔╝██║   ██║█████╔╝ █████╔╝ ██║█████╗  \n", style=ACCENT)
        logo.append("██╔═══╝ ██║   ██║██╔═██╗ ██╔═██╗ ██║██╔══╝  \n", style=ACCENT)
        logo.append("██║     ╚██████╔╝██║  ██╗██║  ██╗██║███████╗\n", style=ACCENT)
        logo.append("╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝", style=ACCENT)
    else:
        logo.append("POKKIE", style="bold #a78bfa")

    subtitle = Text()
    subtitle.append("blazingly fast • ", style=MUTED)
    subtitle.append("groq-powered", style=OK)
    subtitle.append(" • type ", style=MUTED)
    subtitle.append("/help", style="bold #fbbf24")
    subtitle.append(" for commands", style=MUTED)

    status = Text()
    status.append("model ", style=MUTED)
    status.append(f"{model}  ", style="bold #a78bfa")
    status.append(" │ api ", style=MUTED)
    status.append("✔ connected" if has_key else "✖ missing key (/settings)",
                  style=OK if has_key else BAD)

    body = Group(
        Align.center(logo),
        Padding(Align.center(subtitle), (1, 0, 0, 0)),
        Align.center(status),
    )

    console.print()
    console.print(Panel(body, border_style="#7c3aed", box=box.HEAVY, padding=(1, 2)))
    console.print()


def help_table() -> None:
    t = Table(box=box.ROUNDED, border_style="#a78bfa", show_header=True,
              header_style="bold #f472b6", title="Pokkie Commands",
              title_style="bold #a78bfa")
    t.add_column("Command", style="bold #22d3ee", no_wrap=True)
    t.add_column("Description", style="white")
    t.add_row("/help", "Show all commands")
    t.add_row("/settings", "Configure Groq API key, system prompt & tools")
    t.add_row("/model", "Switch active Groq model")
    t.add_row("/models", "List available models")
    t.add_row("/tools", "Show installed automation dependencies")
    t.add_row("/doctor", "Diagnose key/network/API problems")
    t.add_row("/clear", "Clear the current conversation")
    t.add_row("/system <text>", "Update the system prompt inline")
    t.add_row("/exit  /quit", "Exit Pokkie")
    console.print(t)


def models_table(models: list[str], current: str) -> None:
    t = Table(box=box.SIMPLE_HEAVY, border_style="#334155", show_header=True)
    t.add_column("", width=2, justify="center")
    t.add_column("Model", style="bold #e2e8f0")
    t.add_column("Use", style="#94a3b8")
    for model in models:
        active = model == current
        t.add_row("●" if active else "○", model, "active" if active else f"/model → choose {models.index(model) + 1}")
    console.print(t)


def user_prompt_prefix() -> str:
    return "❯ "


def render_user(text: str) -> None:
    console.print(Panel(Text(text, style="white"), title="you",
                        title_align="left", border_style=USER, box=box.ROUNDED))


def render_ai_markdown(text: str) -> None:
    console.print(Panel(Markdown(text), title="pokkie", title_align="left",
                        border_style=AI, box=box.ROUNDED))


def info(msg: str) -> None:
    console.print(f"[{OK}]›[/] {msg}")


def warn(msg: str) -> None:
    console.print(f"[{WARN}]![/] {msg}")


def error(msg: str) -> None:
    console.print(f"[{BAD}]✖[/] {msg}")


def error_box(title: str, message: str, hints: list[str] | None = None) -> None:
    body = Text()
    body.append(message, style="#fecaca")
    if hints:
        body.append("\n\nTry:\n", style=MUTED)
        for hint in hints:
            body.append(f"  • {hint}\n", style="#e2e8f0")
    console.print(Panel(body, title=title, title_align="left", border_style="#ef4444", box=box.ROUNDED))


def section(title: str) -> None:
    console.print()
    console.rule(f"[bold #a78bfa]{title}[/]", style="#334155")
