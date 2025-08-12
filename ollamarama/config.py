from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ModelOptions:
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repeat_penalty": self.repeat_penalty,
        }


@dataclass
class AppConfig:
    api_base: str
    models: Dict[str, str]
    default_model: str
    prompt: List[str]
    personality: str
    options: ModelOptions
    mcp_servers: Dict[str, Any] | None = None


def load_config(path: str | Path = "config.json") -> AppConfig:
    p = Path(path)
    # If the path is not absolute, resolve relative to this file's directory
    if not p.is_absolute():
        base_dir = Path(__file__).parent.parent.parent  # workspace root
        candidate = base_dir / p
        if candidate.exists():
            p = candidate
        else:
            # fallback to package directory (ollamarama/)
            package_dir = Path(__file__).parent.parent
            candidate2 = package_dir / p
            if candidate2.exists():
                p = candidate2
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    api_base: str = raw.get("api_base", "http://localhost:11434")
    models: Dict[str, str] = raw.get("models", {})
    default_model: str = raw.get("default_model", next(iter(models), ""))
    prompt: List[str] = raw.get(
        "prompt",
        [
            "you are ",
            ". speak in the first person and never break character. keep your responses relatively brief and to the point.",
        ],
    )
    personality: str = raw.get(
        "personality",
        "an open source AI chatbot named Ollamarama, powered by Ollama.",
    )

    opts_raw = raw.get("options", {})
    options = ModelOptions(
        temperature=float(opts_raw.get("temperature", 0.7)),
        top_p=float(opts_raw.get("top_p", 0.9)),
        repeat_penalty=float(opts_raw.get("repeat_penalty", 1.0)),
    )

    mcp_servers: Dict[str, Any] | None = raw.get("mcp_servers")

    return AppConfig(
        api_base=api_base,
        models=models,
        default_model=default_model,
        prompt=prompt,
        personality=personality,
        options=options,
        mcp_servers=mcp_servers,
    )
