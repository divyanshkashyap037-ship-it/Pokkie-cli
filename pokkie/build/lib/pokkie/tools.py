"""Tool implementations for Pokkie automation."""
from __future__ import annotations
import json
import os
import platform
import subprocess
import time
import ctypes
import webbrowser
from pathlib import Path
from typing import Any

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


def _focus_browser_window():
    """Bring the browser window to the foreground (Windows only)."""
    if platform.system() != "Windows":
        return False
    try:
        import pygetwindow as gw
        keywords = ["chrome", "edge", "firefox", "brave", "opera", "safari"]
        for kw in keywords:
            wins = gw.getWindowsWithTitle(kw)
            if wins:
                win = wins[0]
                try:
                    win.activate()
                    time.sleep(0.25)
                    return True
                except Exception:
                    continue
        return False
    except Exception:
        return False


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path to the file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to create or overwrite"},
                    "content": {"type": "string", "description": "Text content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (defaults to current directory)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_browser",
            "description": "Open a URL in the default system web browser (Chrome, Edge, Firefox, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to open"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Open a URL in the browser. Use this to go to a specific page. The browser must already be open or this will open it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click at screen coordinates (x, y). Use screenshot first to find coordinates. Common workflow: screenshot → analyze → click at coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X coordinate (pixels from left)"},
                    "y": {"type": "number", "description": "Y coordinate (pixels from top)"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type",
        "description": "Type text into the currently focused input field. Works in any app including the browser. Use Tab to move between fields, Enter to submit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "interval": {"type": "number", "description": "Seconds between keystrokes (default 0.05)"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": "Take a screenshot of the current screen. Use this to see what's on screen and find coordinates for clicking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to save the screenshot (optional)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_type",
            "description": "Type text using system keyboard automation. Use this to fill fields in any app.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "interval": {"type": "number", "description": "Seconds between keystrokes (default 0.05)"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a single keyboard key (e.g. enter, tab, escape, space).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name: enter, tab, escape, space, etc."}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command on the system and return the output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"}
                },
                "required": ["command"]
            }
        }
    },
]


def execute_tool(name: str, arguments: dict) -> str:
    if name == "read_file":
        return read_file(**arguments)
    if name == "write_file":
        return write_file(**arguments)
    if name == "list_directory":
        return list_directory(**arguments)
    if name == "open_browser":
        return open_browser(**arguments)
    if name == "browser_navigate":
        return browser_navigate(**arguments)
    if name == "browser_click":
        return browser_click(**arguments)
    if name == "browser_type":
        return browser_type(**arguments)
    if name == "browser_screenshot":
        return browser_screenshot(**arguments)
    if name == "keyboard_type":
        return keyboard_type(**arguments)
    if name == "press_key":
        return press_key(**arguments)
    if name == "run_command":
        return run_command(**arguments)
    return f"Unknown tool: {name}"


# --- File operations ---

def read_file(path: str) -> str:
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return f"Error: file not found: {p}"
        if p.is_dir():
            return f"Error: {p} is a directory, not a file."
        return p.read_text(encoding="utf-8")
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


def list_directory(path: str = "") -> str:
    try:
        p = Path(path or ".").expanduser().resolve()
        if not p.exists():
            return f"Error: path not found: {p}"
        if not p.is_dir():
            return f"Error: {p} is not a directory."
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        lines = []
        for item in items:
            tag = "[DIR]" if item.is_dir() else "     "
            lines.append(f"{tag} {item.name}")
        return "\n".join(lines) or "(empty)"
    except Exception as e:
        return f"Error listing directory: {e}"


# --- Browser automation (lightweight, uses system browser + pyautogui) ---

def open_browser(url: str) -> str:
    try:
        webbrowser.open(url)
        time.sleep(0.5)
        _focus_browser_window()
        return f"Opened {url} in default browser."
    except Exception as e:
        return f"Error opening browser: {e}"


def browser_navigate(url: str) -> str:
    try:
        webbrowser.open(url)
        time.sleep(0.5)
        _focus_browser_window()
        return f"Opened {url} in browser."
    except Exception as e:
        return f"Error navigating browser: {e}"


def browser_click(x: float, y: float) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        _focus_browser_window()
        pyautogui.click(x, y)
        return f"Clicked at coordinates ({x}, {y})."
    except Exception as e:
        return f"Error clicking: {e}"


def browser_type(text: str, interval: float = 0.05) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        _focus_browser_window()
        pyautogui.typewrite(text, interval=interval)
        return f"Typed text into focused input."
    except Exception as e:
        return f"Error typing: {e}"


def browser_screenshot(path: str = "") -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        p = Path(path or "screenshot.png").expanduser().resolve()
        img = pyautogui.screenshot()
        img.save(str(p))
        return f"Screenshot saved to {p}"
    except Exception as e:
        return f"Error taking screenshot: {e}"


# --- Keyboard automation ---

def keyboard_type(text: str, interval: float = 0.05) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        pyautogui.typewrite(text, interval=interval)
        return f"Typed text via keyboard."
    except Exception as e:
        return f"Error typing: {e}"


def press_key(key: str) -> str:
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui not installed. Run: pip install pyautogui"
    try:
        pyautogui.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key: {e}"


# --- System commands ---

def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if err:
            out = (out + "\n" if out else "") + err
        return out if out else "(command completed with no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 60s."
    except Exception as e:
        return f"Error running command: {e}"


def get_tool_instructions() -> str:
    missing = []
    if not PYAUTOGUI_AVAILABLE:
        missing.append("browser_click, browser_type, browser_screenshot, keyboard_type, press_key")

    lines = [
        "You are an AI agent with direct control of the user's computer. Use the tools below when they help accomplish the user's task.",
        "",
        "RULES:",
        "- If the user asks a simple question (like 'hi', 'how are you', 'what is 2+2'), just answer normally. DO NOT use tools.",
        "- Only use tools when the task actually requires controlling the computer, browsing the web, or manipulating files.",
        "- NEVER say 'I cannot do this' or 'I am an AI'. Use the tools.",
        "- If a tool result shows an error, try a different approach.",
        "- For browser tasks: open_browser(url) → browser_type(text) → press_key('enter') → browser_screenshot(path).",
        "- Do NOT call both open_browser and browser_navigate for the same URL. Pick ONE.",
        "- For file tasks: use list_directory, read_file, write_file directly.",
        "- For keyboard tasks: use keyboard_type and press_key.",
        "- Always show the user what you are doing before doing it.",
        "",
        "**File operations:**",
        "- `read_file(path)` — read a file's contents",
        "- `write_file(path, content)` — create or overwrite a file",
        "- `list_directory(path)` — list files in a directory",
        "",
        "**Browser automation (uses system browser + keyboard):**",
        "- `open_browser(url)` — open a URL in the default browser",
        "- `browser_navigate(url)` — open a URL in the browser",
        "- `browser_click(x, y)` — click at screen coordinates (use screenshot first to find coords)",
        "- `browser_type(text)` — type into the focused input field",
        "- `browser_screenshot(path)` — screenshot the current screen",
        "",
        "**Keyboard automation:**",
        "- `keyboard_type(text, interval=0.05)` — type text via keyboard",
        "- `press_key(key)` — press a key (enter, tab, escape, space, etc.)",
        "",
        "**System:**",
        "- `run_command(command)` — execute a shell command",
        "",
        "When you need to use a tool, output a tool call in this exact JSON format:",
        '```json',
        '{"name": "tool_name", "arguments": {"param": "value"}}',
        '```',
        "I will execute it and return the result. You can call multiple tools in sequence.",
        "",
        "Example browser workflow for generating an image:",
        '1. open_browser({"url": "https://ideogram.ai"})',
        '2. browser_type({"text": "A cute cat wearing sunglasses"})',
        '3. press_key({"key": "enter"})',
        '4. browser_screenshot({"path": "cat.png"})',
    ]

    if missing:
        lines.append(f"\nNote: some tools are unavailable because dependencies are missing: {', '.join(missing)}.")

    return "\n".join(lines)
