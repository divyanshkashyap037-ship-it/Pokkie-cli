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


def banner(provider_label: str, model: str, has_key: bool) -> None:
    logo = Text()
    if console.width >= 78:
        logo.append("██████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗███████╗\n", style=ACCENT)
        logo.append("██╔══██╗██╔═══██╗██║ ██╔╝██║ ██╔╝██║██╔════╝\n", style=ACCENT)
        logo.append("██████╔╝██║   ██║█████╔╝ █████╔╝ ██║█████╗  \n", style=ACCENT)
        logo.append("██╔═══╝ ██║   ██║██╔═██╗ ██╔═██╗ ██║██╔══╝  \n", style=ACCENT)
        logo.append("██║     ╚██████╔╝██║  ██╗██║  ██╗██║███████╗\n", style=ACCENT)
        logo.append("╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝", style=ACCENT)
    else:
        logo.append("POKKIE", style=ACCENT)

    subtitle = Text()
    subtitle.append("blazingly fast • ", style=MUTED)
    subtitle.append(provider_label, style=OK)
    subtitle.append(" • type ", style=MUTED)
    subtitle.append("/help", style="bold #fbbf24")
    subtitle.append(" for commands", style=MUTED)

    status = Text()
    status.append("model ", style=MUTED)
    status.append(f"{model}  ", style=ACCENT)
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
              header_style="bold #f472b6", title="Pokkie Commands", title_style=ACCENT)
    t.add_column("Command", style="bold #22d3ee", no_wrap=True)
    t.add_column("Description", style="white")
    for cmd, desc in [
        ("/help", "Show all commands"),
        ("/settings", "Configure API keys, system prompt, tools"),
        ("/provider", "Switch AI provider (Groq / NVIDIA NIM)"),
        ("/model", "Switch model for the current provider"),
        ("/models", "List models for the current provider"),
        ("/tools", "Show installed automation dependencies"),
        ("/doctor", "Diagnose key/network/API problems"),
        ("/clear", "Clear the current conversation"),
        ("/system <text>", "Update the system prompt inline"),
        ("/exit  /quit", "Exit Pokkie"),
    ]:
        t.add_row(cmd, desc)
    console.print(t)


def models_table(models: list[str], current: str) -> None:
    t = Table(box=box.SIMPLE_HEAVY, border_style="#334155", show_header=True)
    t.add_column("", width=2, justify="center")
    t.add_column("Model", style="bold #e2e8f0")
    t.add_column("Use", style="#94a3b8")
    for model in models:
        active = model == current
        t.add_row("●" if active else "○", model,
                  "active" if active else f"/model → choose {models.index(model) + 1}")
    console.print(t)


def providers_table(providers: dict, current: str) -> None:
    t = Table(box=box.SIMPLE_HEAVY, border_style="#334155", show_header=True, title="Providers")
    t.add_column("", width=2, justify="center")
    t.add_column("Id", style="bold #22d3ee")
    t.add_column("Label", style="white")
    for i, (pid, meta) in enumerate(providers.items(), 1):
        active = pid == current
        t.add_row("●" if active else str(i), pid, meta["label"] + ("  (active)" if active else ""))
    console.print(t)


def user_prompt_prefix() -> str:
    return "❯ "


def render_user(text: str) -> None:
    console.print(Panel(Text(text, style="white"), title="you",
                        title_align="left", border_style=USER, box=box.ROUNDED))


def render_ai_markdown(text: str) -> None:
    console.print(Panel(Markdown(text), title="pokkie",
                        title_align="left", border_style=AI, box=box.ROUNDED))


def section(title: str) -> None:
    console.print()
    console.print(Text(title, style=ACCENT))


def info(msg: str) -> None:
    console.print(f"[{OK}]›[/] {msg}")


def warn(msg: str) -> None:
    console.print(f"[{WARN}]⚠[/] {msg}")


def error(msg: str) -> None:
    console.print(f"[{BAD}]✖[/] {msg}")


def error_box(title: str, message: str, hints: list[str] | None = None) -> None:
    body = Text()
    body.append(message + "\n", style="white")
    if hints:
        body.append("\nTry:\n", style=MUTED)
        for h in hints:
            body.append(f"  • {h}\n", style=MUTED)
    console.print(Panel(body, title=title, title_align="left",
                        border_style=BAD, box=box.ROUNDED))
