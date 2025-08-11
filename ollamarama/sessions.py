from __future__ import annotations

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from typing import Iterable, Optional


def create_keybindings() -> KeyBindings:
    kb = KeyBindings()

    @kb.add("escape", "enter")
    def _(event) -> None:
        event.current_buffer.insert_text("\n")

    @kb.add("enter")
    def _(event) -> None:
        event.current_buffer.validate_and_handle()

    return kb


def create_session(
    *,
    key_bindings: KeyBindings,
    words: Optional[Iterable[str]] = None,
    multiline: bool = True,
) -> PromptSession:
    completer = WordCompleter(list(words) if words else [])
    return PromptSession(
        key_bindings=key_bindings,
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
        multiline=multiline,
        completer=completer,
    )

