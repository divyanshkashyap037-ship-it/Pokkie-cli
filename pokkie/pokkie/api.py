"""Multi-provider OpenAI-compatible streaming chat client (Groq + NVIDIA NIM).

Uses only urllib so no extra deps are needed.
"""
from __future__ import annotations
import json
import re
from typing import Any, Iterator
import urllib.request
import urllib.error

from .tools import TOOLS
from .config import PROVIDERS

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 Pokkie/0.4"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class ApiError(Exception):
    pass


# Back-compat alias so old code paths keep working
GroqError = ApiError


def _strip_html(value: str) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _format_http_error(provider: str, code: int, body: str) -> str:
    lowered = body.lower()
    try:
        payload = json.loads(body)
        message = payload.get("error", {}).get("message") or payload.get("message") or payload.get("detail")
        if message:
            return f"{provider} API error {code}: {message}"
    except Exception:
        pass

    if "cloudflare" in lowered or "error 1010" in lowered or "access denied" in lowered:
        return (
            f"{provider} rejected this request with Cloudflare access control (HTTP {code}). "
            "Pokkie sends browser-like headers, but the provider is blocking the current "
            "network/VPN/proxy/IP. Try another network, disable VPN/proxy, regenerate the key, "
            "or run /doctor."
        )

    clean = _strip_html(body) or "No response body returned."
    return f"HTTP {code}: {clean[:420]}"


def _endpoint(cfg_or_provider: Any, path: str) -> str:
    if isinstance(cfg_or_provider, str):
        base = PROVIDERS[cfg_or_provider]["base_url"]
    else:
        base = PROVIDERS[cfg_or_provider.get("provider", "groq")]["base_url"]
    return base.rstrip("/") + path


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


def check_connection(provider: str, api_key: str) -> tuple[bool, str]:
    label = PROVIDERS[provider]["label"]
    if not api_key:
        return False, f"{label} API key is missing. Open /settings and paste a key from {PROVIDERS[provider]['keys_url']}."

    req = _request(_endpoint(provider, "/models"), api_key)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            payload = json.loads(body)
            count = len(payload.get("data", []))
            return True, f"Connected to {label}. {count or 'Several'} models are reachable."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return False, _format_http_error(label, e.code, body)
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, f"Connection check failed: {e}"


def stream_chat(
    provider: str,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
) -> Iterator[str]:
    label = PROVIDERS[provider]["label"]
    if not api_key:
        raise ApiError(f"{label} API key not set. Use /settings to add it.")

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }).encode("utf-8")

    req = _request(_endpoint(provider, "/chat/completions"), api_key, payload=payload, stream=True)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise ApiError(_format_http_error(label, e.code, body)) from e
    except urllib.error.URLError as e:
        raise ApiError(f"Network error: {e.reason}") from e

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
                message = obj["error"].get("message", "Unknown stream error")
                raise ApiError(f"{label} stream error: {message}")
            delta = obj["choices"][0]["delta"].get("content")
            if delta:
                yield delta
        except ApiError:
            raise
        except Exception:
            continue


def chat_completion(
    provider: str,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    tools: list[dict] | None = None,
    tool_choice: str = "auto",
) -> dict:
    label = PROVIDERS[provider]["label"]
    if not api_key:
        raise ApiError(f"{label} API key not set. Use /settings to add it.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    req = _request(_endpoint(provider, "/chat/completions"), api_key,
                   payload=json.dumps(payload).encode("utf-8"), stream=False)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise ApiError(_format_http_error(label, e.code, body)) from e
    except urllib.error.URLError as e:
        raise ApiError(f"Network error: {e.reason}") from e


def chat_with_tools(
    provider: str,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tool_rounds: int = 20,
) -> tuple[str, list[str]]:
    from .tools import execute_tool

    logs: list[str] = []
    messages = list(messages)
    last_tool_calls: list[str] = []

    for round_num in range(max_tool_rounds):
        try:
            response = chat_completion(provider, api_key, model, messages, temperature, tools=TOOLS)
        except ApiError as e:
            err_msg = str(e)
            if "400" in err_msg or "Failed to call a function" in err_msg:
                messages.append({
                    "role": "user",
                    "content": "The previous tool call failed. Try a different approach or continue without tools.",
                })
                logs.append(f"[retry] round {round_num + 1}: {err_msg[:120]}")
                continue
            raise

        choice = response.get("choices", [{}])[0]
        msg = choice.get("message", {}) or {}
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            return msg.get("content", "") or "", logs

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
                "content": "You already tried those exact tool calls. Try something different or finish.",
            })
            last_tool_calls = []
            continue
        last_tool_calls = call_signatures

        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls})

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
