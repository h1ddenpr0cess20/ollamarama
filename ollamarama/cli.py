from __future__ import annotations

import argparse
import copy
from typing import Optional

from .app import App
from .client import OllamaClient


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ollamarama",
        description="Terminal chatbot for interacting with local LLMs via Ollama. Supports customization of model, persona, and response parameters to tailor the chat experience.",
    )

    persona_group = parser.add_mutually_exclusive_group()
    persona_group.add_argument(
        "-p",
        "--persona",
        type=str,
        help="Set initial persona/system style (string)",
    )
    persona_group.add_argument(
        "-s",
        "--stock",
        action="store_true",
        help="Start with stock (no persona) settings",
    )
    persona_group.add_argument(
        "-c",
        "--custom",
        type=str,
        help="Set custom persona/system style (string)",
    )

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="Model key or full model name",
    )
    parser.add_argument(
        "-b",
        "--api-base",
        type=str,
        help="Override Ollama API base URL",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        help="Initial temperature (0-1)",
    )
    parser.add_argument(
        "-tp",
        "--top-p",
        dest="top_p",
        type=float,
        help="Initial top_p (0-1)",
    )
    parser.add_argument(
        "-r",
        "--repeat-penalty",
        dest="repeat_penalty",
        type=float,
        help="Repeat penalty (0-2)",
    )

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
            # Try matching by shortened name (removing :latest suffix)
            short_to_full = {app._shorten_model_name(name): name for name in app.models.keys()}
            if args.model in short_to_full:
                full_model_name = short_to_full[args.model]
                app.default_model = full_model_name
                app.model = app.models[full_model_name]
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
    elif args.custom:
        app.personality = args.custom

    
    app.start()
