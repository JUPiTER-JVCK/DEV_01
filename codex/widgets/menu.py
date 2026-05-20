"""Numbered menu widget — renders a styled menu and reads user choice."""

from rich.text import Text
from rich.table import Table
from rich import box

from ..renderer import Renderer


class MenuItem:
    def __init__(self, key: str, label: str, hint: str = "",
                 badge: str = "", disabled: bool = False):
        self.key = key
        self.label = label
        self.hint = hint
        self.badge = badge
        self.disabled = disabled


def render_menu(r: Renderer, items: list[MenuItem], compact: bool = False,
                mode: str = "auto") -> None:
    t = r.theme
    spacing = 0 if compact else 1

    for i, item in enumerate(items):
        if item.disabled:
            line = Text()
            line.append(f"  {item.key}  ", style="dim")
            line.append(item.label, style="dim")
            r.pad_print(line, mode)
            continue

        line = Text()
        line.append(f"  [{item.key}]", style=t.s("menu_number"))
        line.append("  ", style="")
        line.append(item.label, style=t.s("menu_item"))

        if item.badge:
            line.append(f"  {item.badge}", style=t.s("accent"))

        if item.hint:
            line.append(f"  — {item.hint}", style=t.s("menu_hint"))

        r.pad_print(line, mode)

        if spacing and i < len(items) - 1:
            r.blank()


def render_key_hints(r: Renderer, hints: list[tuple[str, str]], mode: str = "auto") -> None:
    """Render a row of keyboard shortcut hints at the bottom of a screen."""
    t = r.theme
    line = Text()
    for i, (key, desc) in enumerate(hints):
        if i > 0:
            line.append("  ", style="")
        line.append(f"[{key}]", style=t.s("menu_key"))
        line.append(f" {desc}", style=t.s("menu_hint"))
    r.pad_print(line, mode)


def prompt_choice(r: Renderer, choices: list[str], prompt: str = "Choose") -> str:
    """Prompt user for a choice and return it (lowercase stripped)."""
    t = r.theme
    valid = [c.lower() for c in choices]
    opts = "/".join(choices)
    r.blank()
    r.pad_print(
        Text(f"  {prompt} [{opts}]: ", style=t.s("menu_hint")), "auto"
    )
    while True:
        try:
            raw = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "q"
        if raw in valid or raw == "q":
            return raw
        if not raw:
            return choices[0].lower() if choices else "q"


def prompt_input(r: Renderer, prompt: str, default: str = "") -> str:
    """Prompt for freeform text input."""
    t = r.theme
    dflt = f" [{default}]" if default else ""
    r.blank()
    r.pad_print(Text(f"  {prompt}{dflt}: ", style=t.s("menu_hint")), "auto")
    try:
        raw = input().strip()
        return raw if raw else default
    except (EOFError, KeyboardInterrupt):
        return default
