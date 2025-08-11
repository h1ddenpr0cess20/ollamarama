from __future__ import annotations

import copy
import logging
from typing import Dict, List

from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

from .client import OllamaClient
from .config import AppConfig, load_config
from .render import get_console, print_error, print_info, print_markdown, print_help
from .sessions import create_keybindings, create_session


class App:
    def __init__(self) -> None:
        logging.basicConfig(
            filename="ollamarama.log",
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
        )

        self.console = get_console()
        self.messages: List[Dict[str, str]] = []

        self.config: AppConfig = load_config("config.json")
        self.models: Dict[str, str] = self.config.models
        self.default_model: str = self.config.default_model
        self.model: str = self.models.get(self.default_model, self.default_model)

        self.client = OllamaClient(self.config.api_base)

        self.options: Dict[str, float] = self.config.options.to_dict()
        # Keep a safe copy for resets
        self.defaults: Dict[str, float] = copy.deepcopy(self.options)

        self.default_personality: str = self.config.personality
        self.personality: str = self.default_personality
        self.prompt_tpl = self.config.prompt

        kb = create_keybindings()
        self.session = create_session(
            key_bindings=kb,
            words=[
                "/help",
                "/exit",
                "/quit",
                "/reset",
                "/clear",
                "/stock",
                "/persona",
                "/custom",
                "/model",
                "/temperature",
                "/top_p",
                "/repeat_penalty",
            ],
            multiline=True,
        )

        self.persona_session = create_session(
            key_bindings=kb,
            words=["a sarcastic jerk"],
            multiline=True,
        )

        self.custom_session = create_session(key_bindings=kb, multiline=True)

        self.model_session = create_session(
            key_bindings=kb,
            words=self.models.keys(),
        )

    @staticmethod
    def _visible_after_think(text: str) -> str:
        """Return only the content after a closing </think> tag.

        - If one or more </think> tags exist (case-insensitive), return the
          substring after the last closing tag.
        - If a <think> appears without a closing tag, return an empty string
          to avoid exposing hidden reasoning.
        - If no think tags exist, return the text unchanged.
        """
        if not text:
            return text

        lower = text.lower()
        open_idx = lower.find("<think>")
        close_idx = lower.rfind("</think>")

        if close_idx != -1:
            after = close_idx + len("</think>")
            return text[after:].lstrip()

        # If there's an opening tag but no closing tag, hide everything
        if open_idx != -1 and close_idx == -1:
            return ""

        return text

    def set_prompt(self, *, persona: bool | str = False, custom: bool = False) -> None:
        self.messages.clear()
        system = None

        if persona:
            if isinstance(persona, bool):
                personality = self.persona_session.prompt("Persona: ")
            else:
                personality = persona
            if personality:
                system = f"{self.prompt_tpl[0]}{personality}{self.prompt_tpl[1]}"
                logging.info(f"Persona set to {system}")
        elif custom:
            system = self.custom_session.prompt("System prompt: ")
            if system:
                logging.info(f"Custom system prompt set: {system}")
        else:
            logging.info("Stock model settings applied")
            print_info(self.console, "Stock model settings applied")

        if system:
            self.messages.append({"role": "system", "content": system})
            self.messages.append({"role": "user", "content": "introduce yourself"})
            response = self.respond_stream(self.messages)
            # respond_stream already prints progressively; ensure newline after.
            self.console.print()

    def respond(self, message: List[Dict[str, str]]) -> str:
        try:
            text = self.client.chat(model=self.model, messages=message, options=self.options)
        except Exception as e:
            err = f"Failed to get response: {e}"
            print_error(self.console, err)
            logging.exception(err)
            return "An error occurred. Check logs."

        # Hide reasoning: only expose content after </think>
        visible = self._visible_after_think(text)

        self.messages.append({"role": "assistant", "content": visible})
        logging.info(f"Bot: {visible}")

        if len(self.messages) > 24:
            if self.messages[0]["role"] == "system":
                self.messages.pop(1)
            else:
                self.messages.pop(0)
        return visible

    def respond_stream(self, message: List[Dict[str, str]]) -> str:
        """Stream a response and render progressively with Rich Live.

        Applies the same think-tag hiding policy as respond(): if the stream
        starts with a <think> block, suppress output until the first closing
        </think> tag and then reveal only the subsequent content. If an opening
        <think> appears without a closing tag, emit nothing and return an empty
        string.
        """
        total: str = ""
        visible_accum: str = ""
        suppress_until_close: bool | None = None
        emitted_upto: int = 0

        try:
            interrupted = False
            # Use Rich Live to continuously update a Markdown renderable
            spinner = Spinner("dots", text="thinking…", style="gold3")
            showing_spinner = True
            with Live(
                spinner,
                console=self.console,
                refresh_per_second=24,
            ) as live:
                try:
                    for chunk in self.client.chat_stream(
                        model=self.model, messages=message, options=self.options
                    ):
                        # Accumulate raw text
                        total += chunk

                        # Decide suppression on first content
                        if suppress_until_close is None:
                            leading = total.lstrip().lower()
                            suppress_until_close = leading.startswith("<think>")

                        if suppress_until_close:
                            lower = total.lower()
                            close_idx = lower.find("</think>")
                            if close_idx != -1:
                                # Start emitting after the first closing tag
                                start = close_idx + len("</think>")
                                # Emit everything after close (that hasn't been emitted)
                                to_emit = total[start:]
                                if to_emit:
                                    visible_accum += to_emit
                                    live.update(
                                        Markdown(visible_accum, code_theme="monokai", style="gold3"),
                                        refresh=True,
                                    )
                                emitted_upto = len(total)
                                suppress_until_close = False
                            else:
                                # Still suppressing; keep spinner visible
                                if not showing_spinner:
                                    live.update(spinner, refresh=True)
                                    showing_spinner = True
                                continue
                        else:
                            # Emit any newly added text
                            to_emit = total[emitted_upto:]
                            if to_emit:
                                visible_accum += to_emit
                                if showing_spinner:
                                    showing_spinner = False
                                live.update(
                                    Markdown(visible_accum, code_theme="monokai", style="gold3"),
                                    refresh=True,
                                )
                                emitted_upto = len(total)
                except KeyboardInterrupt:
                    interrupted = True
                    # Gracefully stop streaming on Ctrl+C
                    pass
        except Exception as e:
            err = f"Failed to stream response: {e}"
            print_error(self.console, err)
            logging.exception(err)
            return ""

        if 'interrupted' in locals() and interrupted:
            logging.info("Streaming interrupted by user (Ctrl+C)")
            # Add a newline so the next prompt doesn't collide with the live area
            self.console.print()
            # Subtle status to indicate stop
            self.console.print("[stopped]", style="italic dim")

        # Finalize visible text respecting think rules
        if suppress_until_close:
            # Opening <think> without closing: hide all so far
            visible = ""
        else:
            visible = visible_accum

        # Persist assistant message to history when non-empty or not an interruption-only think block
        if not ('interrupted' in locals() and interrupted and not visible.strip()):
            self.messages.append({"role": "assistant", "content": visible})
            logging.info(f"Bot: {visible}")

        if len(self.messages) > 24:
            if self.messages[0]["role"] == "system":
                self.messages.pop(1)
            else:
                self.messages.pop(0)

        return visible

    def reset(self) -> None:
        logging.info("Bot reset")
        self.model = self.models.get(self.default_model, self.default_model)
        self.options = copy.deepcopy(self.defaults)
        self.console.print("Please wait while the model loads...", style="bold")
        try:
            self.set_prompt(persona=self.personality)
        except Exception as e:
            self.console.print(str(e))
            raise

    def change_model(self, *, reset: bool = False) -> None:
        if reset:
            self.model = self.models.get(self.default_model, self.default_model)
            print_info(self.console, f"Model set to {self.model}")
            logging.info(f"Model changed to {self.model}")
            return

        self.console.print(f"[bold green]Current model[/]: [bold]{self.model}[/]")
        self.console.print(
            f"[bold green]Available models[/]: {', '.join(sorted(list(self.models)))}"
        )
        model = self.model_session.prompt("Enter model name: ")
        if model in self.models:
            self.model = self.models[model]
            print_info(self.console, f"Model set to {self.model}")
            logging.info(f"Model changed to {self.model}")

    def change_option(self, option: str) -> None:
        ranges = {"temperature": (0, 1), "top_p": (0, 1), "repeat_penalty": (0, 2)}
        try:
            input_value = self.console.input("Input new value: ")
            if not input_value.strip():
                print_error(self.console, "No value entered, nothing changed")
                return
            value = float(input_value)
            low, high = ranges[option]
            if low <= value <= high:
                self.options[option] = value
                print_info(self.console, f"{option.capitalize()} set to {value}")
            else:
                print_error(self.console, f"Invalid value. Must be between {low} and {high}")
        except ValueError:
            print_error(self.console, "Invalid input. Please enter a numeric value.")

    def help_menu(self) -> None:
        print_help(self.console, "help.txt")

    def start(self) -> None:
        self.reset()

        commands = {
            "/quit": lambda: exit(),
            "/exit": lambda: exit(),
            "/help": lambda: self.help_menu(),
            "/reset": lambda: self.reset(),
            "/stock": lambda: self.set_prompt(),
            "/clear": lambda: self.console.clear(),
            "/persona": lambda: self.set_prompt(persona=True),
            "/custom": lambda: self.set_prompt(custom=True),
            "/model": lambda: self.change_model(),
            "/model reset": lambda: self.change_model(reset=True),
            "/temperature": lambda: self.change_option("temperature"),
            "/top_p": lambda: self.change_option("top_p"),
            "/repeat_penalty": lambda: self.change_option("repeat_penalty"),
        }

        while True:
            message = self.session.prompt("> ")
            if message in commands:
                commands[message]()
            elif message is not None:
                self.messages.append({"role": "user", "content": message})
                logging.info(f"User: {message}")
                # Stream the answer instead of waiting for full response
                response = self.respond_stream(self.messages)
                # Ensure newline after streaming output and keep markdown print for consistency if desired
                # print_markdown(self.console, response)
