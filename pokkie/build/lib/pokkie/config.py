"""Config management for Pokkie. Stored at ~/.pokkie_config.json"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".pokkie_config.json"
HISTORY_PATH = Path.home() / ".pokkie_history"

# Providers ----------------------------------------------------------------

PROVIDERS: dict[str, dict[str, Any]] = {
    "groq": {
        "label": "Groq (LPU, ultra-fast)",
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "keys_url": "https://console.groq.com/keys",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "qwen/qwen3-32b",
            "deepseek-r1-distill-llama-70b",
            "gemma2-9b-it",
        ],
        "default_model": "llama-3.3-70b-versatile",
    },
    "nvidia": {
        "label": "NVIDIA NIM (free tier — nvapi-* key)",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env": "NVIDIA_API_KEY",
        "keys_url": "https://build.nvidia.com/settings/api-keys",
        "models": [
            "meta/llama-3.3-70b-instruct",
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-8b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "nvidia/llama-3.3-nemotron-super-49b-v1",
            "deepseek-ai/deepseek-r1",
            "mistralai/mixtral-8x22b-instruct-v0.1",
            "mistralai/mistral-large-2-instruct",
            "qwen/qwen2.5-coder-32b-instruct",
            "qwen/qwen2.5-7b-instruct",
            "google/gemma-2-27b-it",
            "microsoft/phi-3.5-mini-instruct",
        ],
        "default_model": "meta/llama-3.3-70b-instruct",
    },
}

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "system_prompt": (
        "You are Pokkie, a concise, expert AI terminal assistant and coding agent. "
        "Prefer code blocks. Use tools when the task needs the filesystem, shell, or browser."
    ),
    "temperature": 0.7,
    "version": "0.4.0",
    "enable_tools": True,
    "keys": {"groq": "", "nvidia": ""},
    # Legacy field kept for backwards compatibility with 0.2/0.3 configs
    "groq_api_key": "",
}


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_CONFIG.copy()

    merged = {**DEFAULT_CONFIG, **data}
    # Migration: legacy `groq_api_key` -> keys.groq
    keys = dict(DEFAULT_CONFIG["keys"])
    keys.update(merged.get("keys") or {})
    if not keys.get("groq") and merged.get("groq_api_key"):
        keys["groq"] = merged["groq_api_key"]
    # Env override (never persisted)
    for pid, meta in PROVIDERS.items():
        env_val = os.environ.get(meta["key_env"])
        if env_val and not keys.get(pid):
            keys[pid] = env_val
    merged["keys"] = keys
    if merged.get("provider") not in PROVIDERS:
        merged["provider"] = "groq"
    return merged


def save_config(cfg: dict[str, Any]) -> None:
    # Don't persist env-injected keys accidentally: still fine — user chose to save.
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


def current_provider(cfg: dict[str, Any]) -> dict[str, Any]:
    return PROVIDERS[cfg.get("provider", "groq")]


def current_key(cfg: dict[str, Any]) -> str:
    return (cfg.get("keys") or {}).get(cfg.get("provider", "groq"), "") or ""


def current_models(cfg: dict[str, Any]) -> list[str]:
    return current_provider(cfg)["models"]
