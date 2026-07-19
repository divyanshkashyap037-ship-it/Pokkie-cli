"""Groq streaming chat client (uses HTTP directly, no SDK required)."""
from __future__ import annotations
import json
import re
from typing import Any, Iterator
import urllib.request
import urllib.error

from .tools import TOOLS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 Pokkie/0.2"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class GroqError(Exception):
    pass


def _strip_html(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _format_http_error(code: int, body: str) -> str:
    """Return a short, terminal-safe error instead of dumping HTML pages."""
    lowered = body.lower()

    try:
        payload = json.loads(body)
        message = payload.get("error", {}).get("message") or payload.get("message")
        if message:
            return f"Groq API error {code}: {message}"
    except Exception:
        pass

    if "cloudflare" in lowered or "error 1010" in lowered or "access denied" in lowered:
        return (
            "Groq rejected this request with Cloudflare access control (HTTP "
            f"{code}). Pokkie now sends safer browser-like headers, but if this "
            "still appears, Groq is blocking your current network/VPN/proxy/IP. "
            "Try another network, disable VPN/proxy, regenerate your Groq key, "
            "or run /doctor for a quick connection check."
        )

    clean = _strip_html(body)
    if not clean:
        clean = "No response body returned."
    return f"HTTP {code}: {clean[:420]}"


def _request(url: str, api_key: str, payload: bytes | None = None, stream: bool = False):
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream, application/json" if stream else "application/json",
    }
    method = "POST" if payload is not None else "GET"
    if payload is not None:
        headers["Content-Type"] = "application/json"

    return urllib.request.Request(url, data=payload, headers=headers, method=method)


def check_connection(api_key: str) -> tuple[bool, str]:
    """Check whether Groq is reachable without printing secrets or raw HTML."""
    if not api_key:
        return False, "Groq API key is missing. Open /settings and paste a key from https://console.groq.com/keys."

    req = _request(GROQ_MODELS_URL, api_key)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            payload = json.loads(body)
            count = len(payload.get("data", []))
            return True, f"Connected to Groq. {count or 'Several'} models are reachable."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return False, _format_http_error(e.code, body)
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, f"Connection check failed: {e}"


def stream_chat(
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
) -> Iterator[str]:
    """Yield text deltas from the Groq streaming chat API."""
    if not api_key:
        raise GroqError("Groq API key not set. Use /settings to add it.")

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }).encode("utf-8")

    req = _request(GROQ_URL, api_key, payload=payload, stream=True)

    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise GroqError(_format_http_error(e.code, body)) from e
    except urllib.error.URLError as e:
        raise GroqError(f"Network error: {e.reason}") from e

    for raw_line in resp:
        line = raw_line.decode("utf-8", errors="ignore").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            obj = json.loads(data)
            if obj.get("error"):
                message = obj["error"].get("message", "Unknown Groq stream error")
                raise GroqError(f"Groq stream error: {message}")
            delta = obj["choices"][0]["delta"].get("content")
            if delta:
                yield delta
        except GroqError:
            raise
        except Exception:
            continue


def chat_completion(
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    tools: list[dict] | None = None,
    tool_choice: str = "auto",
) -> dict:
    """Non-streaming chat completion that supports tool calls."""
    if not api_key:
        raise GroqError("Groq API key not set. Use /settings to add it.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    req = _request(GROQ_URL, api_key, payload=json.dumps(payload).encode("utf-8"), stream=False)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise GroqError(_format_http_error(e.code, body)) from e
    except urllib.error.URLError as e:
        raise GroqError(f"Network error: {e.reason}") from e


def chat_with_tools(
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tool_rounds: int = 15,
) -> tuple[str, list[str]]:
    """Run a tool loop: send messages, execute any tool calls, repeat until text response.

    Returns (final_text, tool_logs).
    """
    from .tools import execute_tool

    logs: list[str] = []
    messages = list(messages)
    last_tool_calls: list[str] = []

    for round_num in range(max_tool_rounds):
        try:
            response = chat_completion(api_key, model, messages, temperature, tools=TOOLS)
        except GroqError as e:
            err_msg = str(e)
            if "400" in err_msg or "Failed to call a function" in err_msg:
                recovery_msg = {
                    "role": "user",
                    "content": "The previous tool call failed with a server error. "
                               "Please try a different approach or continue without tools.",
                }
                messages.append(recovery_msg)
                logs.append(f"[retry] round {round_num + 1}: model error, retrying with recovery message")
                continue
            raise

        choice = response.get("choices", [{}])[0]
        msg = choice.get("message", {})
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            content = msg.get("content", "") or ""
            return content, logs

        call_signatures = []
        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            call_signatures.append(f"{name}({args})")

        if call_signatures == last_tool_calls:
            logs.append(f"[dedup] skipped duplicate tool calls: {call_signatures}")
            messages.append({
                "role": "user",
                "content": "You already tried those exact tool calls. Please try something different or finish.",
            })
            last_tool_calls = []
            continue

        last_tool_calls = call_signatures
        assistant_msg: dict = {"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls}
        messages.append(assistant_msg)

        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}

            logs.append(f"[tool] {name}({args})")
            result = execute_tool(name, args)
            logs.append(f"[result] {result[:500]}")

            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", ""),
                "content": result,
            })

    return "I reached the maximum number of tool calls. Here is what I did:\n" + "\n".join(logs), logs
