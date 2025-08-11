from __future__ import annotations

import argparse
import copy
from typing import Optional

from .app import App
from .client import OllamaClient


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ollamarama",
        description="Terminal chatbot for local LLMs via Ollama",
    )

    persona_group = parser.add_mutually_exclusive_group()
    persona_group.add_argument(
        "--persona",
        type=str,
        help="Set initial persona/system style (string)",
    )
    persona_group.add_argument(
        "--stock",
        action="store_true",
        help="Start with stock (no persona) settings",
    )

    parser.add_argument("--model", type=str, help="Model key or full model name")
    parser.add_argument("--api-base", type=str, help="Override Ollama API base URL")
    parser.add_argument("--temperature", type=float, help="Initial temperature (0-1)")
    parser.add_argument("--top-p", dest="top_p", type=float, help="Initial top_p (0-1)")
    parser.add_argument("--repeat-penalty", dest="repeat_penalty", type=float, help="Repeat penalty (0-2)")

    args = parser.parse_args()

    app = App()

    # API base override
    if args.api_base:
        app.console.print(f"Using API base: {args.api_base}", style="green")
        app.client = OllamaClient(args.api_base)

    # Options overrides
    updated_options = False
    for key in ("temperature", "top_p", "repeat_penalty"):
        val: Optional[float] = getattr(args, key)
        if val is not None:
            app.options[key] = float(val)
            updated_options = True
    if updated_options:
        app.defaults = copy.deepcopy(app.options)

    # Model override
    if args.model:
        if args.model in app.models:
            app.default_model = args.model
            app.model = app.models[args.model]
        else:
            # Try matching by value
            values = app.models.values()
            if args.model in values:
                # find its first key
                for k, v in app.models.items():
                    if v == args.model:
                        app.default_model = k
                        break
                app.model = args.model
            else:
                app.console.print(
                    f"[red]Unknown model[/]: {args.model}. Available: {', '.join(sorted(app.models))}"
                )

    # Persona/stock
    if args.stock:
        app.personality = ""
    elif args.persona:
        app.personality = args.persona

    app.start()
