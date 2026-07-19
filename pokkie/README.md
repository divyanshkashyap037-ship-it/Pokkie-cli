# Pokkie ⚡ v0.4

Blazingly fast, open-source AI terminal assistant & coding agent.
Now with **multi-provider support**: **Groq** (LPU) *and* **NVIDIA NIM** (free tier).

## What's new in 0.4
- 🔀 **Multi-provider**: switch between Groq and NVIDIA NIM with `/provider`
- 🆓 **NVIDIA NIM free-tier models** (Llama 3.3 70B, Llama 3.1 405B, Nemotron 70B, DeepSeek-R1, Mixtral 8x22B, Qwen 2.5 Coder 32B, Gemma 2 27B, and more)
- 🛠️ **Better coding tools**: `search_files` (glob), `grep` (recursive content search), `edit_file` (surgical find/replace), `append_file`, `python_eval`, `run_command` with `cwd`
- 🎹 **Key combos**: `press_key("ctrl+s")`, etc.
- 🐧 **Fixed cross-platform install** — `pygetwindow` is now Windows-only via a platform marker (previously broke `pip install` on macOS/Linux)
- 🧹 Refreshed Groq model list (removed deprecated `mixtral-8x7b-32768` / `llama3-*-8192`); added `llama-4-scout`, `llama-4-maverick`, `qwen3-32b`, `openai/gpt-oss-*`
- 🩺 `/doctor` now reports for whichever provider is active
- ⚙️ Config migrates automatically from 0.2/0.3
- 🌱 `GROQ_API_KEY` / `NVIDIA_API_KEY` environment variables are picked up automatically

## Install

### Windows
1. Download & unzip `pokkie-cli.zip`
2. Double-click `install.bat`
3. Open a new terminal → `pokkie`

### macOS / Linux
```bash
unzip pokkie-cli.zip && cd pokkie
bash install.sh
pokkie
```

### From source
```bash
pip install ".[automation]"
pokkie
```

Core deps only (no keyboard/screenshot automation):
```bash
pip install .
```

## First run
Pokkie opens `/settings` on first launch and asks for keys.
- **Groq** — free key at <https://console.groq.com/keys>
- **NVIDIA NIM** — free key at <https://build.nvidia.com/settings/api-keys> (format `nvapi-…`)

You only need **one** to get started. Switch anytime with `/provider`.

## Providers & models

### Groq (LPU, ultra-fast)
`llama-3.3-70b-versatile` · `llama-3.1-8b-instant` · `openai/gpt-oss-120b` · `openai/gpt-oss-20b` ·
`meta-llama/llama-4-scout-17b-16e-instruct` · `meta-llama/llama-4-maverick-17b-128e-instruct` ·
`qwen/qwen3-32b` · `deepseek-r1-distill-llama-70b` · `gemma2-9b-it`

### NVIDIA NIM (free tier)
`meta/llama-3.3-70b-instruct` · `meta/llama-3.1-405b-instruct` · `meta/llama-3.1-70b-instruct` ·
`meta/llama-3.1-8b-instruct` · `nvidia/llama-3.1-nemotron-70b-instruct` ·
`nvidia/llama-3.3-nemotron-super-49b-v1` · `deepseek-ai/deepseek-r1` ·
`mistralai/mixtral-8x22b-instruct-v0.1` · `mistralai/mistral-large-2-instruct` ·
`qwen/qwen2.5-coder-32b-instruct` · `qwen/qwen2.5-7b-instruct` ·
`google/gemma-2-27b-it` · `microsoft/phi-3.5-mini-instruct`

## Tools (coding + automation)

| Tool | Description |
|------|-------------|
| `read_file(path)` | Read any file (auto-truncates > 200k chars) |
| `write_file(path, content)` | Create / overwrite a file |
| `append_file(path, content)` | Append to a file |
| `edit_file(path, find, replace)` | Surgical find/replace in a file |
| `list_directory(path)` | List folder contents |
| `search_files(pattern, path?)` | Recursive glob (e.g. `*.py`) — capped at 500 |
| `grep(pattern, path?, regex?)` | Recursive content search — capped at 200 hits |
| `run_command(command, cwd?)` | Shell (120s timeout, per-directory) |
| `python_eval(code)` | Quick Python snippet in a subprocess |
| `open_browser(url)` | Open URL in default browser |
| `browser_click(x, y)` | Click at coordinates (needs `pyautogui`) |
| `browser_type(text)` | Type into focused input |
| `browser_screenshot(path?)` | Take a screenshot |
| `keyboard_type(text)` | Type anywhere on your system |
| `press_key(key)` | Press a key or combo (`ctrl+s`, `alt+tab`, …) |

Auto-ignored during search/grep: `.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`, `.mypy_cache`, `.pytest_cache`.

## Commands
| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/settings` | Configure API keys, system prompt & tools |
| `/provider` | Switch AI provider (Groq / NVIDIA NIM) |
| `/model` | Switch model for the current provider |
| `/models` | List models for the current provider |
| `/tools` | Show installed automation dependencies |
| `/doctor` | Diagnose key/network/API issues |
| `/clear` | Wipe conversation |
| `/system <t>` | Set a system prompt inline |
| `/exit` | Quit |

## Config
Stored at `~/.pokkie_config.json` (chmod 600). Old `groq_api_key` fields are migrated automatically. Environment variables `GROQ_API_KEY` and `NVIDIA_API_KEY` are picked up on load.

## Troubleshooting: HTTP 403 / Cloudflare 1010
Pokkie sends browser-like headers and shows short, terminal-safe errors. If Cloudflare still blocks you:
1. `/doctor`
2. Disable VPN/proxy or try another network
3. Regenerate the key
4. `/provider` to switch to NVIDIA NIM as a fallback

## Uninstall
```bash
pip uninstall pokkie
```
