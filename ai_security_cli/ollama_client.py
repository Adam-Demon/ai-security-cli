"""Thin client for calling a local Ollama chat model, with timeout and
retry/backoff handling. Isolated here so the target backend can be
swapped (e.g. a different local inference server) without touching the
runner or scoring logic."""

import json
import time
from typing import Optional

import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


def call_ollama(model: str, system_prompt: Optional[str], user_prompt: str,
                 timeout: float, retries: int) -> tuple[str, Optional[str], float]:
    """
    Call the local Ollama chat API.

    Returns (output_text, error, latency_ms). On failure after all
    retries, output_text is "" and error describes the last failure.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {"model": model, "messages": messages, "stream": False}

    last_error = None
    for attempt in range(retries + 1):
        start = time.monotonic()
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
            resp.raise_for_status()
            latency_ms = (time.monotonic() - start) * 1000
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            return text, None, latency_ms
        except requests.exceptions.Timeout:
            last_error = f"timeout after {timeout}s (attempt {attempt + 1}/{retries + 1})"
        except requests.exceptions.ConnectionError as e:
            last_error = f"connection error (attempt {attempt + 1}/{retries + 1}): {e}"
        except requests.exceptions.HTTPError as e:
            last_error = f"HTTP error (attempt {attempt + 1}/{retries + 1}): {e}"
        except (json.JSONDecodeError, KeyError) as e:
            last_error = f"malformed response (attempt {attempt + 1}/{retries + 1}): {e}"
        if attempt < retries:
            time.sleep(min(2 ** attempt, 5))

    return "", last_error, 0.0
