from __future__ import annotations

import requests
from typing import Any, Dict, List, Iterator, Optional


class OllamaClient:
    def __init__(self, api_base: str) -> None:
        self.api_url = api_base.rstrip("/") + "/api/chat"

    def chat(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any],
        stream: bool = False,
        timeout: int = 360,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": options,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        response = requests.post(self.api_url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        text: str = data["message"]["content"]
        if (
            isinstance(text, str)
            and text.startswith('"')
            and text.endswith('"')
            and text.count('"') == 2
        ):
            text = text.strip('"')
        return text.strip()

    def chat_stream(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any],
        timeout: int = 360,
    ) -> Iterator[str]:
        """Yield content chunks from Ollama chat stream.

        Uses JSONL responses with a final done object. Yields only non-empty
        content strings from the "message.content" field.
        """
        import json

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": options,
        }
        with requests.post(
            self.api_url,
            json=payload,
            timeout=timeout,
            stream=True,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict) and obj.get("error"):
                    raise RuntimeError(obj.get("error"))
                if obj.get("done"):
                    break
                msg = obj.get("message") or {}
                chunk = msg.get("content") or ""
                if chunk:
                    yield chunk

    def chat_with_tools(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        options: Dict[str, Any],
        tools: List[Dict[str, Any]],
        tool_choice: Optional[str] = "auto",
        timeout: int = 360,
    ) -> Dict[str, Any]:
        """Call /api/chat with tools and return the full JSON response."""
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
            "tools": tools,
        }
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice

        response = requests.post(self.api_url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
