# Pokkie ⚡ v0.3

Blazingly fast, open-source AI terminal assistant powered by the **Groq API**.

## Features
- 🚀 Ultra-fast streaming (Groq LPU inference)
- 🎨 Beautiful terminal UI (Rich + prompt_toolkit)
- 🔀 Instant model switching (`/model`)
- 🛠️ **Computer automation** — read/write files, control your browser, automate keyboard (no heavy Chromium download)
- 🩺 `/doctor` command for key/network/API diagnostics
- 🧼 Clean HTTP errors — no more huge Cloudflare HTML dumps
- ⚙️ Persistent config (`~/.pokkie_config.json`)
- 💬 Slash commands: `/help`, `/settings`, `/model`, `/models`, `/tools`, `/doctor`, `/clear`, `/system`, `/exit`
- 🌍 Global CLI — just type `pokkie`

## Install

### Windows
1. Download & unzip `pokkie.zip`
2. Double-click `install.bat` — it upgrades old installs too
3. Open a new terminal → type `pokkie`

### macOS / Linux
```bash
unzip pokkie.zip && cd pokkie
bash install.sh
pokkie
```

### From source
```bash
pip install .
pokkie
```

## First Run
Pokkie will ask for your **Groq API key** (get a free one at <https://console.groq.com/keys>).
You can update it anytime with `/settings`.

## Automation Tools
Pokkie can control your computer to complete tasks. Enable/disable them in `/settings`.

| Tool | Description |
|------|-------------|
| `read_file(path)` | Read any file |
| `write_file(path, content)` | Create or overwrite a file |
| `list_directory(path)` | List folder contents |
| `open_browser(url)` | Open a URL in your default browser (Chrome, Edge, Firefox) |
| `browser_navigate(url)` | Open a URL in the browser |
| `browser_click(x, y)` | Click at screen coordinates |
| `browser_type(text)` | Type into the focused input field |
| `browser_screenshot(path)` | Screenshot the current screen |
| `keyboard_type(text)` | Type anywhere on your system |
| `press_key(key)` | Press enter, tab, escape, etc. |
| `run_command(cmd)` | Run a shell command |

### Example: Create a React Learning Poster
```
you: create a react learning poster for beginners
pokkie: I'll generate a prompt and create it for you...
[tool] open_browser({"url": "https://ideogram.ai"})
[tool] browser_type("A colorful React learning poster for beginners showing hooks, components, and state management...")
[tool] press_key({"key": "enter"})
[tool] browser_screenshot({"path": "react_poster.png"})
pokkie: Poster generated and screenshot saved to react_poster.png
```

## Commands
| Command       | Description                             |
| ------------- | --------------------------------------- |
| `/help`       | Show all commands                       |
| `/settings`   | Configure API key, system prompt & tools |
| `/model`      | Switch Groq model                       |
| `/models`     | List available models                   |
| `/tools`      | Show installed automation dependencies  |
| `/doctor`     | Diagnose key/network/API issues         |
| `/clear`      | Wipe conversation                       |
| `/system <t>` | Set a system prompt inline              |
| `/exit`       | Quit                                    |

## Fix: `HTTP 403` / Cloudflare `Error 1010`

Pokkie v0.3 hides the raw HTML error and sends safer request headers. If Groq still returns **Cloudflare Access denied**, Groq is blocking the current network signature, VPN/proxy, or IP — not your prompt.

Try this:
1. Run `/doctor` inside Pokkie.
2. Disable VPN/proxy, or try a mobile hotspot / different network.
3. Create a fresh Groq key at <https://console.groq.com/keys> and update it with `/settings`.
4. If it still fails, contact Groq support and mention Cloudflare Error 1010.

## Uninstall
```bash
pip uninstall pokkie
```
