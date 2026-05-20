from __future__ import annotations

import json
from typing import Any, Generator

import httpx


class APIError(Exception):
    pass


class Client:
    def __init__(self, base_url: str, api_key: str = "", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.Client(headers=headers, timeout=httpx.Timeout(timeout))

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def list_models(self) -> list[dict[str, Any]]:
        resp = self._client.get(self._url("models"))
        if resp.is_error:
            raise APIError(
                f"Failed to list models ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        return data.get("data", [])

    def stream_chat(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> Generator[str, None, None]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        with self._client.stream("POST", self._url("chat/completions"), json=payload) as resp:
            if resp.is_error:
                raise APIError(
                    f"Chat completion failed ({resp.status_code}): {resp.text}"
                )
            for line in resp.iter_lines():
                line = line.strip()
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
