"""Config management for Pokkie. Stored at ~/.pokkie_config.json"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".pokkie_config.json"
HISTORY_PATH = Path.home() / ".pokkie_history"

DEFAULT_CONFIG: dict[str, Any] = {
    "groq_api_key": "",
    "model": "llama-3.3-70b-versatile",
    "system_prompt": "You are Pokkie, a concise, expert AI terminal assistant. Answer clearly. Prefer code blocks when relevant.",
    "temperature": 0.7,
    "version": "0.2.0",
    "enable_tools": True,
}

AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "deepseek-r1-distill-llama-70b",
]


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        merged = {**DEFAULT_CONFIG, **data}
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass


def update_config(**kwargs: Any) -> dict[str, Any]:
    cfg = load_config()
    cfg.update(kwargs)
    save_config(cfg)
    return cfg
