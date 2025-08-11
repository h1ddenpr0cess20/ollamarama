from __future__ import annotations

import requests
from typing import Any, Dict, List


class OllamaClient:
    def __init__(self, api_base: str) -> None:
        self.api_url = api_base.rstrip("/") + "/api/chat"

    def chat(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        options: Dict[str, Any],
        stream: bool = False,
        timeout: int = 180,
    ) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": options,
        }

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

