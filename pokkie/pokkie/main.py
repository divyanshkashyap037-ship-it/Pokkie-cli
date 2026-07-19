"""Pokkie main entrypoint - `pokkie` command."""
from __future__ import annotations
import getpass
import sys
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings

from . import ui
from .config import HISTORY_PATH, load_config, save_config, update_config, AVAILABLE_MODELS
from .api import stream_chat, chat_with_tools, GroqError, check_connection
from .tools import get_tool_instructions

SLASH = ["/help", "/settings", "/model", "/models", "/tools", "/doctor", "/clear", "/system", "/exit", "/quit"]

PT_STYLE = Style.from_dict({
    "prompt": "#a78bfa bold",
    "bottom-toolbar": "bg:#111827 #94a3b8",
    "": "#e2e8f0",
})


def choose_from_list(title: str, items: list[str], current: str | None = None) -> str | None:
    ui.section(title)
    ui.models_table(items, current or "")
    ui.console.print()
    try:
        raw = input("select #: ").strip()
        if not raw:
            return None
        idx = int(raw) - 1
        if 0 <= idx < len(items):
            return items[idx]
    except (ValueError, EOFError, KeyboardInterrupt):
        return None
    return None


def cmd_settings(cfg: dict) -> dict:
    ui.console.print()
    ui.console.print(Panel.fit(
        Text.from_markup(
            "[bold #a78bfa]Pokkie Settings[/]\n"
            "[dim]Get a free Groq API key at https://console.groq.com/keys[/]\n"
            "[dim]Paste is hidden while typing. Leave blank to keep current values.[/]"
        ),
        border_style="#a78bfa", box=box.ROUNDED,
    ))

    masked = (cfg.get("groq_api_key", "")[:6] + "…") if cfg.get("groq_api_key") else "not set"
    ui.console.print(f"[bold #22d3ee]Groq API key[/] [dim](current: {masked})[/]")
    try:
        new_key = getpass.getpass("  new key: ").strip()
    except (EOFError, KeyboardInterrupt):
        new_key = ""
    except Exception:
        new_key = input("  new key: ").strip()
    if new_key:
        cfg["groq_api_key"] = new_key

    ui.console.print(f"\n[bold #22d3ee]System prompt[/] [dim](current: {cfg.get('system_prompt','')[:60]}…)[/]")
    try:
        new_sys = input("  new prompt: ").strip()
    except (EOFError, KeyboardInterrupt):
        new_sys = ""
    if new_sys:
        cfg["system_prompt"] = new_sys

    ui.console.print(f"\n[bold #22d3ee]Enable tools[/] [dim](current: {cfg.get('enable_tools', True)})[/]")
    try:
        tool_raw = input("  enable tools (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        tool_raw = ""
    if tool_raw in ("y", "n"):
        cfg["enable_tools"] = tool_raw == "y"

    save_config(cfg)
    ui.info("settings saved to ~/.pokkie_config.json")
    return cfg


def cmd_model(cfg: dict) -> dict:
    picked = choose_from_list("Select a Groq model", AVAILABLE_MODELS, cfg.get("model"))
    if picked:
        cfg = update_config(model=picked)
        ui.info(f"model switched → [bold #a78bfa]{picked}[/]")
    else:
        ui.warn("no change")
    return cfg


def cmd_doctor(cfg: dict) -> None:
    ui.section("Pokkie Doctor")
    ui.info("checking Groq API reachability…")
    ok, message = check_connection(cfg.get("groq_api_key", ""))
    if ok:
        ui.info(message)
        return

    ui.error_box(
        "Connection problem",
        message,
        hints=[
            "Run /settings and make sure the Groq key is valid.",
            "Disable VPN/proxy or try a mobile hotspot/another network if Cloudflare 1010 appears.",
            "Open https://console.groq.com/keys and create a fresh key if the old one was revoked.",
        ],
    )


def cmd_tools(cfg: dict) -> None:
    ui.section("Tools Status")
    from .tools import PYAUTOGUI_AVAILABLE
    ui.info(f"pyautogui (keyboard + browser): {'installed' if PYAUTOGUI_AVAILABLE else 'missing — run: pip install pyautogui'}")
    ui.info(f"Tools enabled: {cfg.get('enable_tools', True)}")


def stream_response(cfg: dict, messages: list[dict]) -> str:
    buf: list[str] = []
    spinner = Spinner("dots12", text=Text(f" thinking with {cfg['model']}…", style="dim #94a3b8"), style="#a78bfa")

    try:
        with Live(spinner, console=ui.console, refresh_per_second=24, transient=True) as live:
            first = True
            for delta in stream_chat(
                api_key=cfg["groq_api_key"],
                model=cfg["model"],
                messages=messages,
                temperature=cfg.get("temperature", 0.7),
            ):
                buf.append(delta)
                if first:
                    first = False
                text = "".join(buf)
                live.update(Panel(Markdown(text), title=f"pokkie · {cfg['model']}",
                                  title_align="left", border_style=ui.AI, box=box.ROUNDED))
    except GroqError as e:
        message = str(e)
        if "Cloudflare" in message or "HTTP 403" in message:
            ui.error_box(
                "Groq access denied",
                message,
                hints=[
                    "Run /doctor to verify the key and network.",
                    "Turn off VPN/proxy or try a different connection.",
                    "If the Groq website works but API calls are blocked, contact Groq support with the Cloudflare 1010 detail.",
                ],
            )
        else:
            ui.error(message)
        return ""
    except KeyboardInterrupt:
        ui.warn("interrupted")

    final = "".join(buf)
    if final:
        ui.render_ai_markdown(final)
    return final


def run_with_tools(cfg: dict, messages: list[dict]) -> tuple[str, list[str]]:
    """Run the tool loop and return (final_text, tool_logs)."""
    spinner = Spinner("dots12", text=Text(f" thinking with {cfg['model']}…", style="dim #94a3b8"), style="#a78bfa")
    try:
        with Live(spinner, console=ui.console, refresh_per_second=24, transient=True) as live:
            return chat_with_tools(
                api_key=cfg["groq_api_key"],
                model=cfg["model"],
                messages=messages,
                temperature=cfg.get("temperature", 0.7),
            )
    except GroqError as e:
        ui.error(str(e))
        return "", []


def run() -> int:
    cfg = load_config()
    ui.console.clear()
    ui.banner(cfg["model"], bool(cfg.get("groq_api_key")))

    if not cfg.get("groq_api_key"):
        ui.warn("no Groq API key configured. running /settings…")
        cfg = cmd_settings(cfg)

    history: list[dict] = []

    completer = WordCompleter(SLASH, ignore_case=True, sentence=True)
    kb = KeyBindings()

    def toolbar() -> str:
        tool_status = "tools:on" if cfg.get("enable_tools", True) else "tools:off"
        return f" model: {cfg.get('model')}  |  {tool_status}  |  /help  /model  /doctor  /clear  |  Ctrl+C exits "

    session: PromptSession = PromptSession(
        history=FileHistory(str(HISTORY_PATH)),
        completer=completer,
        auto_suggest=AutoSuggestFromHistory(),
        key_bindings=kb,
        style=PT_STYLE,
        complete_while_typing=True,
        bottom_toolbar=toolbar,
    )

    while True:
        try:
            text = session.prompt(ui.user_prompt_prefix()).strip()
        except (KeyboardInterrupt, EOFError):
            ui.console.print("\n[dim]bye ✨[/]")
            return 0

        if not text:
            continue

        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("/exit", "/quit"):
                ui.console.print("[dim]bye ✨[/]")
                return 0
            if cmd == "/help":
                ui.help_table()
                continue
            if cmd == "/settings":
                cfg = cmd_settings(cfg)
                continue
            if cmd == "/model":
                cfg = cmd_model(cfg)
                continue
            if cmd == "/models":
                ui.models_table(AVAILABLE_MODELS, cfg["model"])
                continue
            if cmd == "/doctor":
                cmd_doctor(cfg)
                continue
            if cmd == "/tools":
                cmd_tools(cfg)
                continue
            if cmd == "/clear":
                history.clear()
                ui.console.clear()
                ui.banner(cfg["model"], bool(cfg.get("groq_api_key")))
                ui.info("conversation cleared")
                continue
            if cmd == "/system":
                if arg:
                    cfg = update_config(system_prompt=arg)
                    ui.info("system prompt updated")
                else:
                    ui.warn("usage: /system <prompt text>")
                continue
            ui.error(f"unknown command: {cmd}. try /help")
            continue

        history.append({"role": "user", "content": text})

        base_prompt = cfg.get("system_prompt", "")
        tool_instructions = get_tool_instructions() if cfg.get("enable_tools", True) else ""
        system_prompt = (tool_instructions + "\n\n" + base_prompt).strip() if tool_instructions else base_prompt

        messages = [{"role": "system", "content": system_prompt}] + history

        if cfg.get("enable_tools", True):
            reply, logs = run_with_tools(cfg, messages)
            if logs:
                tool_names = []
                for log in logs:
                    if log.startswith("[tool] "):
                        tool_names.append(log[7:].split("(")[0])
                unique_tools = list(dict.fromkeys(tool_names))
                ui.info(f"tools used: {', '.join(unique_tools)}")
            if reply:
                ui.render_ai_markdown(reply)
                history.append({"role": "assistant", "content": reply})
        else:
            reply = stream_response(cfg, messages)
            if reply:
                history.append({"role": "assistant", "content": reply})


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
