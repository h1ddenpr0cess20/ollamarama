from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown


def get_console() -> Console:
    return Console(width=120, highlight=False)


def print_markdown(console: Console, text: str) -> None:
    console.print(Markdown(text, code_theme="monokai"), style="gold3")


def print_info(console: Console, text: str) -> None:
    console.print(text, style="green")


def print_error(console: Console, text: str) -> None:
    console.print(text, style="red")


def print_help(console: Console, path: str = "help.txt") -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            console.print(f.read())
    except Exception as e:
        print_error(console, f"Failed to load help: {e}")

