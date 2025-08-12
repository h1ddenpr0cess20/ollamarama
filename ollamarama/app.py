from __future__ import annotations

import copy
import logging
import os
from typing import Any, Dict, List

from rich.live import Live
from rich.markdown import Markdown
from rich.spinner import Spinner

from .client import OllamaClient
from .config import AppConfig, load_config
from .render import get_console, print_error, print_info, print_markdown, print_help
from .tools import execute_tool
from .sessions import create_keybindings, create_session
from .fastmcp_client import FastMCPClient


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

        # Tool calling
        self.tools_enabled: bool = True
        self.mcp_client: FastMCPClient | None = None
        self._mcp_tool_names: set[str] = set()
        builtin_schema = self._load_tools_schema()
        mcp_schema: List[Dict[str, Any]] = []
        if self.config.mcp_servers:
            servers = {k: v for k, v in self.config.mcp_servers.items() if v}
            if servers:
                try:
                    self.mcp_client = FastMCPClient(servers)
                    mcp_schema = self.mcp_client.list_tools()
                    for tool in mcp_schema:
                        fn = (tool.get("function") or {}).get("name")
                        if isinstance(fn, str):
                            self._mcp_tool_names.add(fn)
                except Exception as e:
                    print_error(self.console, f"Failed to load tools from MCP server: {e}")
            # If servers dict is empty, mcp_schema remains empty
        # Combine MCP and bundled schema (MCP takes precedence on name clashes)
        combined: List[Dict[str, Any]] = list(mcp_schema)
        for tool in builtin_schema:
            fn = (tool.get("function") or {}).get("name")
            if isinstance(fn, str) and fn not in self._mcp_tool_names:
                combined.append(tool)
        self._tools_schema = combined
        if not self._tools_schema:
            self.tools_enabled = False

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
                "/tools",
                "/copy",
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

    # ---- Tool calling helpers ----
    def toggle_tools(self) -> None:
        self.tools_enabled = not self.tools_enabled
        state = "enabled" if self.tools_enabled else "disabled"
        print_info(self.console, f"Tools {state}")

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if self.mcp_client is not None and name in self._mcp_tool_names:
            return self.mcp_client.call_tool(name, arguments)
        return execute_tool(name, arguments)

    def _load_tools_schema(self, path: str | None = None) -> List[Dict[str, Any]]:
        import json
        from pathlib import Path
        # Try importlib.resources for robust package data access
        try:
            from importlib import resources
            with resources.files("ollamarama.tools").joinpath("schema.json").open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            raise ValueError("schema.json must be a JSON array of tool definitions")
        except Exception:
            # Fallback to filesystem path resolution
            try:
                if path is None:
                    here = Path(__file__).resolve().parent
                    path = str(here / "tools" / "schema.json")
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
                raise ValueError("schema.json must be a JSON array of tool definitions")
            except FileNotFoundError:
                print_info(self.console, "No tools/schema.json found; tool calling disabled")
                self.tools_enabled = False
                return []
            except Exception as e:
                print_error(self.console, f"Failed to load schema.json: {e}")
                self.tools_enabled = False
                return []

    def respond_with_tools(self, message: List[Dict[str, Any]]) -> str:
        """Handle tool-calling loop with Ollama's /api/chat and local tool execution.

        Repeats until the assistant returns content without further tool calls.
        Streams the final assistant message for parity with normal replies.
        """
        try:
            result = self.client.chat_with_tools(
                model=self.model,
                messages=message,
                options=self.options,
                tools=self._tools_schema,
                tool_choice="auto",
            )
        except Exception as e:
            err = f"Failed to get tool-aware response: {e}"
            print_error(self.console, err)
            logging.exception(err)
            return ""

        # Tool loop
        max_iterations = 8
        iterations = 0
        while iterations < max_iterations:
            msg = result.get("message", {})
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                break
            # Append assistant tool_calls message to history as-is
            self.messages.append(msg)
            for call in tool_calls:
                func = (call.get("function") or {})
                name = func.get("name") or ""
                raw_args = func.get("arguments")
                try:
                    # arguments may be stringified JSON or dict
                    if isinstance(raw_args, str):
                        import json as _json

                        args = _json.loads(raw_args) if raw_args.strip() else {}
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    else:
                        args = {}
                except Exception:
                    args = {}
                tool_result = self._execute_tool(name, args)
                # Echo tool result back
                tool_msg: Dict[str, Any] = {
                    "role": "tool",
                    "content": str(tool_result),
                }
                # If an id is present, attach it for threading
                if call.get("id"):
                    tool_msg["tool_call_id"] = call["id"]
                self.messages.append(tool_msg)

            try:
                result = self.client.chat_with_tools(
                    model=self.model,
                    messages=self.messages,
                    options=self.options,
                    tools=self._tools_schema,
                    tool_choice="auto",
                )
            except Exception as e:
                err = f"Failed to continue after tool call: {e}"
                print_error(self.console, err)
                logging.exception(err)
                return ""
            iterations += 1

        # No more tool calls: now stream the final assistant content
        streamed = self.respond_stream(self.messages)

        # After a streamed response, trim and lightly clean tool artifacts
        if len(self.messages) > 24:
            if self.messages[0].get("role") == "system":
                self.messages.pop(1)
            else:
                self.messages.pop(0)
            self.messages[:] = [
                m
                for m in self.messages
                if not (m.get("role") == "tool" or (isinstance(m, dict) and m.get("tool_calls")))
            ]

        return streamed

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
            if self.tools_enabled and self._tools_schema:
                _ = self.respond_with_tools(self.messages)
            else:
                _ = self.respond_stream(self.messages)
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

    def copy_last_response(self) -> None:
        # Find the last assistant message content
        content = None
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant":
                text = msg.get("content", "")
                if text:
                    content = text
                    break
        if not content:
            print_error(self.console, "No assistant response to copy.")
            return

        try:
            import pyperclip  # type: ignore

            pyperclip.copy(content.strip())
            print_info(self.console, "Response copied to clipboard.")
        except Exception:
            print_error(
                self.console,
                "Copy failed. Install pyperclip: pip install pyperclip",
            )

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
            "/copy": lambda: self.copy_last_response(),
            "/temperature": lambda: self.change_option("temperature"),
            "/top_p": lambda: self.change_option("top_p"),
            "/repeat_penalty": lambda: self.change_option("repeat_penalty"),
            "/tools": lambda: self.toggle_tools(),
        }

        while True:
            message = self.session.prompt("> ")
            if message in commands:
                commands[message]()
            elif message is not None:
                self.messages.append({"role": "user", "content": message})
                logging.info(f"User: {message}")
                if self.tools_enabled and self._tools_schema:
                    _ = self.respond_with_tools(self.messages)
                else:
                    _ = self.respond_stream(self.messages)
                # Ensure newline after streaming output and keep markdown print for consistency if desired
                # print_markdown(self.console, response)
