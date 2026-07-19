"""Pokkie main entrypoint — the `pokkie` command."""
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
from .config import (
    HISTORY_PATH, PROVIDERS,
    load_config, save_config, update_config,
    current_provider, current_key, current_models,
)
from .api import stream_chat, chat_with_tools, ApiError, check_connection
from .tools import get_tool_instructions

SLASH = [
    "/help", "/settings", "/provider", "/model", "/models",
    "/tools", "/doctor", "/clear", "/system", "/exit", "/quit",
]

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
            "[dim]Groq keys → https://console.groq.com/keys[/]\n"
            "[dim]NVIDIA NIM keys → https://build.nvidia.com/settings/api-keys (free tier available)[/]\n"
            "[dim]Paste is hidden while typing. Leave blank to keep current value.[/]"
        ),
        border_style="#a78bfa", box=box.ROUNDED,
    ))

    keys = dict(cfg.get("keys") or {})
    for pid, meta in PROVIDERS.items():
        cur = keys.get(pid, "") or ""
        masked = (cur[:6] + "…") if cur else "not set"
        ui.console.print(f"\n[bold #22d3ee]{meta['label']} key[/] [dim](current: {masked})[/]")
        try:
            new_key = getpass.getpass(f"  new {pid} key: ").strip()
        except Exception:
            new_key = input(f"  new {pid} key: ").strip()
        if new_key:
            keys[pid] = new_key
    cfg["keys"] = keys

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


def cmd_provider(cfg: dict) -> dict:
    ids = list(PROVIDERS.keys())
    ui.providers_table(PROVIDERS, cfg.get("provider", "groq"))
    try:
        raw = input("select provider #: ").strip()
        idx = int(raw) - 1
        if 0 <= idx < len(ids):
            pid = ids[idx]
            cfg["provider"] = pid
            cfg["model"] = PROVIDERS[pid]["default_model"]
            save_config(cfg)
            ui.info(f"provider switched → [bold #a78bfa]{pid}[/] · model [bold #a78bfa]{cfg['model']}[/]")
            if not current_key(cfg):
                ui.warn(f"no {pid} API key set — run /settings to add one.")
            return cfg
    except (ValueError, EOFError, KeyboardInterrupt):
        pass
    ui.warn("no change")
    return cfg


def cmd_model(cfg: dict) -> dict:
    picked = choose_from_list(
        f"Select a model for {cfg.get('provider','groq')}",
        current_models(cfg),
        cfg.get("model"),
    )
    if picked:
        cfg = update_config(model=picked)
        ui.info(f"model switched → [bold #a78bfa]{picked}[/]")
    else:
        ui.warn("no change")
    return cfg


def cmd_doctor(cfg: dict) -> None:
    ui.section("Pokkie Doctor")
    pid = cfg.get("provider", "groq")
    ui.info(f"checking {PROVIDERS[pid]['label']} reachability…")
    ok, message = check_connection(pid, current_key(cfg))
    if ok:
        ui.info(message)
        return
    ui.error_box(
        "Connection problem",
        message,
        hints=[
            "Run /settings and confirm the key for this provider.",
            "Disable VPN/proxy or try a mobile hotspot / another network.",
            f"Regenerate a fresh key at {PROVIDERS[pid]['keys_url']}.",
            "Try /provider to switch to the other backend as a fallback.",
        ],
    )


def cmd_tools(cfg: dict) -> None:
    ui.section("Tools Status")
    from .tools import PYAUTOGUI_AVAILABLE
    ui.info(f"pyautogui (keyboard + browser): {'installed' if PYAUTOGUI_AVAILABLE else 'missing — run: pip install pyautogui'}")
    ui.info(f"tools enabled: {cfg.get('enable_tools', True)}")


def stream_response(cfg: dict, messages: list[dict]) -> str:
    buf: list[str] = []
    spinner = Spinner("dots12",
                      text=Text(f" thinking with {cfg['model']}…", style="dim #94a3b8"),
                      style="#a78bfa")
    try:
        with Live(spinner, console=ui.console, refresh_per_second=24, transient=True) as live:
            for delta in stream_chat(
                provider=cfg.get("provider", "groq"),
                api_key=current_key(cfg),
                model=cfg["model"],
                messages=messages,
                temperature=cfg.get("temperature", 0.7),
            ):
                buf.append(delta)
                live.update(Panel(
                    Markdown("".join(buf)),
                    title=f"pokkie · {cfg['model']}",
                    title_align="left", border_style=ui.AI, box=box.ROUNDED,
                ))
    except ApiError as e:
        ui.error_box("API error", str(e),
                     hints=["Run /doctor.", "Check /settings.", "Try /provider to switch backend."])
        return ""
    except KeyboardInterrupt:
        ui.warn("interrupted")
    final = "".join(buf)
    if final:
        ui.render_ai_markdown(final)
    return final


def run_with_tools(cfg: dict, messages: list[dict]) -> tuple[str, list[str]]:
    spinner = Spinner("dots12",
                      text=Text(f" thinking with {cfg['model']}…", style="dim #94a3b8"),
                      style="#a78bfa")
    try:
        with Live(spinner, console=ui.console, refresh_per_second=24, transient=True):
            return chat_with_tools(
                provider=cfg.get("provider", "groq"),
                api_key=current_key(cfg),
                model=cfg["model"],
                messages=messages,
                temperature=cfg.get("temperature", 0.7),
            )
    except ApiError as e:
        ui.error(str(e))
        return "", []


def run() -> int:
    cfg = load_config()
    ui.console.clear()
    ui.banner(current_provider(cfg)["label"], cfg["model"], bool(current_key(cfg)))

    if not current_key(cfg):
        ui.warn(f"no {cfg.get('provider','groq')} API key configured. running /settings…")
        cfg = cmd_settings(cfg)

    history: list[dict] = []

    completer = WordCompleter(SLASH, ignore_case=True, sentence=True)
    kb = KeyBindings()

    def toolbar() -> str:
        tool_status = "tools:on" if cfg.get("enable_tools", True) else "tools:off"
        return (f" {cfg.get('provider','groq')} · {cfg.get('model')}  |  "
                f"{tool_status}  |  /help /provider /model /doctor /clear  |  Ctrl+C exits ")

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
                ui.help_table(); continue
            if cmd == "/settings":
                cfg = cmd_settings(cfg); continue
            if cmd == "/provider":
                cfg = cmd_provider(cfg); continue
            if cmd == "/model":
                cfg = cmd_model(cfg); continue
            if cmd == "/models":
                ui.models_table(current_models(cfg), cfg["model"]); continue
            if cmd == "/doctor":
                cmd_doctor(cfg); continue
            if cmd == "/tools":
                cmd_tools(cfg); continue
            if cmd == "/clear":
                history = []
                ui.info("conversation cleared."); continue
            if cmd == "/system":
                if arg:
                    cfg = update_config(system_prompt=arg)
                    ui.info("system prompt updated.")
                else:
                    ui.warn("usage: /system <prompt text>")
                continue
            ui.warn(f"unknown command: {cmd}. /help for the list.")
            continue

        history.append({"role": "user", "content": text})

        base_prompt = cfg.get("system_prompt", "")
        tool_instructions = get_tool_instructions() if cfg.get("enable_tools", True) else ""
        system_prompt = ((tool_instructions + "\n\n" + base_prompt).strip()
                         if tool_instructions else base_prompt)
        messages = [{"role": "system", "content": system_prompt}] + history

        if cfg.get("enable_tools", True):
            reply, logs = run_with_tools(cfg, messages)
            if logs:
                tool_names = [log[7:].split("(")[0] for log in logs if log.startswith("[tool] ")]
                unique = list(dict.fromkeys(tool_names))
                if unique:
                    ui.info(f"tools used: {', '.join(unique)}")
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
