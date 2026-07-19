"""Tool implementations for Pokkie automation and coding tasks."""
from __future__ import annotations
import fnmatch
import json
import os
import platform
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception:
    PYAUTOGUI_AVAILABLE = False


def _focus_browser_window() -> bool:
    """Bring a browser window to the foreground (Windows only)."""
    if platform.system() != "Windows":
        return False
    try:
        import pygetwindow as gw  # type: ignore
        for kw in ("chrome", "edge", "firefox", "brave", "opera", "safari", "arc"):
            wins = gw.getWindowsWithTitle(kw)
            if wins:
                try:
                    wins[0].activate()
                    time.sleep(0.25)
                    return True
                except Exception:
                    continue
    except Exception:
        pass
    return False


def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


TOOLS: list[dict] = [
    _tool("read_file", "Read the contents of a file from the filesystem.",
          {"path": {"type": "string", "description": "Absolute or relative path"}},
          ["path"]),
    _tool("write_file", "Write content to a file. Creates directories as needed.",
          {"path": {"type": "string"}, "content": {"type": "string"}},
          ["path", "content"]),
    _tool("append_file", "Append content to a file. Creates the file if missing.",
          {"path": {"type": "string"}, "content": {"type": "string"}},
          ["path", "content"]),
    _tool("edit_file", "Replace the first occurrence of `find` with `replace` in a file. Use for targeted code edits.",
          {"path": {"type": "string"}, "find": {"type": "string"}, "replace": {"type": "string"}},
          ["path", "find", "replace"]),
    _tool("list_directory", "List files and folders in a directory.",
          {"path": {"type": "string", "description": "Directory path (defaults to current directory)"}}),
    _tool("search_files", "Recursively find files whose name matches a glob (e.g. '*.py'). Fast — capped at 500 results.",
          {"path": {"type": "string"}, "pattern": {"type": "string", "description": "Glob pattern like *.py"}},
          ["pattern"]),
    _tool("grep", "Recursively search file contents for a substring or regex. Returns file:line matches (capped at 200).",
          {"path": {"type": "string"}, "pattern": {"type": "string"},
           "regex": {"type": "boolean", "description": "Treat pattern as regex (default false)"}},
          ["pattern"]),
    _tool("open_browser", "Open a URL in the default system web browser.",
          {"url": {"type": "string"}}, ["url"]),
    _tool("browser_navigate", "Open a URL in the browser (same as open_browser).",
          {"url": {"type": "string"}}, ["url"]),
    _tool("browser_click", "Click at screen coordinates (x, y). Screenshot first to find coordinates.",
          {"x": {"type": "number"}, "y": {"type": "number"}}, ["x", "y"]),
    _tool("browser_type", "Type text into the currently focused input.",
          {"text": {"type": "string"}, "interval": {"type": "number"}}, ["text"]),
    _tool("browser_screenshot", "Take a screenshot and save it.",
          {"path": {"type": "string"}}),
    _tool("keyboard_type", "Type text via system keyboard automation.",
          {"text": {"type": "string"}, "interval": {"type": "number"}}, ["text"]),
    _tool("press_key", "Press a single key (enter, tab, escape, space, etc.). Use `+` for combos, e.g. 'ctrl+s'.",
          {"key": {"type": "string"}}, ["key"]),
    _tool("run_command", "Execute a shell command. Set `cwd` to run inside a specific directory. Times out at 120s.",
          {"command": {"type": "string"}, "cwd": {"type": "string"}}, ["command"]),
    _tool("python_eval", "Execute a short Python snippet in a subprocess and return stdout+stderr. Use for quick calculations, JSON manipulation, etc.",
          {"code": {"type": "string"}}, ["code"]),
]


def execute_tool(name: str, arguments: dict) -> str:
    fn = _DISPATCH.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return fn(**arguments)
    except TypeError as e:
        return f"Error calling {name}: bad arguments ({e})"


# --- File operations -----------------------------------------------------

def read_file(path: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Error: file not found: {p}"
        if p.is_dir():
            return f"Error: {p} is a directory, not a file."
        data = p.read_text(encoding="utf-8", errors="replace")
        if len(data) > 200_000:
            return data[:200_000] + f"\n… (truncated, total {len(data)} chars)"
        return data
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {p}"
    except Exception as e:
        return f"Error writing file: {e}"


def append_file(path: str, content: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(content)
        return f"Appended {len(content)} chars to {p}"
    except Exception as e:
        return f"Error appending file: {e}"


def edit_file(path: str, find: str, replace: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Error: file not found: {p}"
        original = p.read_text(encoding="utf-8", errors="replace")
        if find not in original:
            return f"Error: `find` snippet not found in {p}. No change written."
        updated = original.replace(find, replace, 1)
        p.write_text(updated, encoding="utf-8")
        return f"Edited {p} (1 replacement)."
    except Exception as e:
        return f"Error editing file: {e}"


def list_directory(path: str = "") -> str:
    try:
        p = Path(path or ".").expanduser().resolve()
        if not p.exists():
            return f"Error: path not found: {p}"
        if not p.is_dir():
            return f"Error: {p} is not a directory."
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        lines = [f"{'[DIR]' if item.is_dir() else '     '} {item.name}" for item in items]
        return "\n".join(lines) or "(empty)"
    except Exception as e:
        return f"Error listing directory: {e}"


_IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".mypy_cache", ".pytest_cache"}


def search_files(pattern: str, path: str = "") -> str:
    try:
        root = Path(path or ".").expanduser().resolve()
        if not root.exists():
            return f"Error: path not found: {root}"
        matches: list[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
            for name in filenames:
                if fnmatch.fnmatch(name, pattern):
                    matches.append(str(Path(dirpath, name)))
                    if len(matches) >= 500:
                        matches.append("… (capped at 500)")
                        return "\n".join(matches)
        return "\n".join(matches) or "(no matches)"
    except Exception as e:
        return f"Error searching files: {e}"


def grep(pattern: str, path: str = "", regex: bool = False) -> str:
    import re
    try:
        root = Path(path or ".").expanduser().resolve()
        if not root.exists():
            return f"Error: path not found: {root}"
        rx = re.compile(pattern) if regex else None
        hits: list[str] = []
        targets: list[Path] = [root] if root.is_file() else []
        if root.is_dir():
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
                for name in filenames:
                    targets.append(Path(dirpath, name))
        for f in targets:
            try:
                if f.stat().st_size > 2_000_000:
                    continue
                with f.open("r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if (rx.search(line) if rx else (pattern in line)):
                            hits.append(f"{f}:{i}: {line.rstrip()[:200]}")
                            if len(hits) >= 200:
                                hits.append("… (capped at 200)")
                                return "\n".join(hits)
            except Exception:
                continue
        return "\n".join(hits) or "(no matches)"
    except Exception as e:
        return f"Error grepping: {e}"


# --- Browser / GUI automation --------------------------------------------

def open_browser(url: str) -> str:
    try:
        webbrowser.open(url)
        time.sleep(0.5)
        _focus_browser_window()
        return f"Opened {url} in default browser."
    except Exception as e:
        return f"Error opening browser: {e}"


def browser_navigate(url: str) -> str:
    return open_browser(url)


def browser_click(x: float, y: float) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        _focus_browser_window()
        pyautogui.click(x, y)
        return f"Clicked at ({x}, {y})."
    except Exception as e:
        return f"Error clicking: {e}"


def browser_type(text: str, interval: float = 0.05) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        _focus_browser_window()
        pyautogui.typewrite(text, interval=interval)
        return "Typed text into focused input."
    except Exception as e:
        return f"Error typing: {e}"


def browser_screenshot(path: str = "") -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        p = Path(path or "screenshot.png").expanduser().resolve()
        pyautogui.screenshot().save(str(p))
        return f"Screenshot saved to {p}"
    except Exception as e:
        return f"Error taking screenshot: {e}"


def keyboard_type(text: str, interval: float = 0.05) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        pyautogui.typewrite(text, interval=interval)
        return "Typed text via keyboard."
    except Exception as e:
        return f"Error typing: {e}"


def press_key(key: str) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        if "+" in key:
            pyautogui.hotkey(*[k.strip() for k in key.split("+")])
        else:
            pyautogui.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key: {e}"


# --- Shell + Python ------------------------------------------------------

def run_command(command: str, cwd: str = "") -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=120, cwd=(cwd or None),
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        combined = out + (("\n" + err) if err and out else err)
        header = f"(exit {result.returncode})\n"
        return header + (combined if combined else "(no output)")
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 120s."
    except Exception as e:
        return f"Error running command: {e}"


def python_eval(code: str) -> str:
    try:
        result = subprocess.run(
            ["python", "-c", code], capture_output=True, text=True, timeout=30,
        )
        out = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
        return f"(exit {result.returncode})\n{out.strip() or '(no output)'}"
    except FileNotFoundError:
        return "Error: `python` not found on PATH."
    except subprocess.TimeoutExpired:
        return "Error: python snippet timed out after 30s."
    except Exception as e:
        return f"Error running python: {e}"


_DISPATCH: dict[str, Any] = {
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "edit_file": edit_file,
    "list_directory": list_directory,
    "search_files": search_files,
    "grep": grep,
    "open_browser": open_browser,
    "browser_navigate": browser_navigate,
    "browser_click": browser_click,
    "browser_type": browser_type,
    "browser_screenshot": browser_screenshot,
    "keyboard_type": keyboard_type,
    "press_key": press_key,
    "run_command": run_command,
    "python_eval": python_eval,
}


def get_tool_instructions() -> str:
    missing = []
    if not PYAUTOGUI_AVAILABLE:
        missing.append("browser_click, browser_type, browser_screenshot, keyboard_type, press_key")

    lines = [
        "You are Pokkie — a coding + automation agent with direct control of the user's computer.",
        "",
        "RULES:",
        "- Simple chit-chat (greetings, math, factual Qs) → answer directly, NO tools.",
        "- Coding tasks → prefer `read_file`, `grep`, `search_files`, `edit_file`, `write_file`, `run_command`.",
        "- Browser/GUI tasks → screenshot → analyze → click/type. Don't call open_browser AND browser_navigate for the same URL.",
        "- If a tool errors, try a different approach — don't repeat the identical call.",
        "- Always describe the action before doing anything destructive.",
        "",
        "File & code tools: read_file, write_file, append_file, edit_file, list_directory, search_files, grep",
        "Shell tools: run_command(command, cwd?), python_eval(code)",
        "Browser tools: open_browser, browser_click, browser_type, browser_screenshot",
        "Keyboard: keyboard_type, press_key (supports 'ctrl+s' combos)",
    ]
    if missing:
        lines.append(f"\nNote: missing dependencies disable: {', '.join(missing)}. Install with `pip install pyautogui`.")
    return "\n".join(lines)
