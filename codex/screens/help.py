"""Help screen — keyboard shortcuts and about CODEX."""

from rich.text import Text

from ..renderer import Renderer
from ..config import Config
from ..widgets.art import SPARK_ART, CODEX_TAGLINE
from ..widgets.menu import prompt_choice


SHORTCUTS = [
    ("[1-9]", "select menu item"),
    ("[q]",   "go back / quit"),
    ("[/]",   "search (from any menu)"),
    ("[b]",   "bookmark current lesson"),
    ("[n]",   "add note to current lesson"),
    ("[s]",   "skip to end of lesson"),
    ("[?]",   "show this help screen"),
    ("Enter", "confirm / next section"),
]


def show(r: Renderer, cfg: Config) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    r.rule("  HELP & ABOUT  ")
    r.blank()

    if cfg.show_word_art:
        art = Text(SPARK_ART, style=t.s("muted"))
        r.pad_print(art, mode)

    title = Text("  CODEX — Interactive Terminal Learning Reference", style=t.s("title"))
    r.pad_print(title, mode)
    r.blank()

    tagline = Text(f"  {CODEX_TAGLINE}", style=t.s("subtitle"))
    r.pad_print(tagline, mode)
    r.blank()

    desc = Text(
        "  CODEX is a forever-reference terminal app covering the full stack —\n"
        "  from the physics of electricity to fiber standards, assembly language,\n"
        "  Linux distributions, and programming languages. Designed for developers\n"
        "  who learn best in the terminal.",
        style=t.s("menu_item"),
        overflow="fold",
    )
    r.pad_print(desc, mode)
    r.blank()

    r.rule("  KEYBOARD SHORTCUTS  ")
    r.blank()

    for key, desc_str in SHORTCUTS:
        line = Text()
        line.append(f"  {key:<10}", style=t.s("menu_key"))
        line.append(f"  {desc_str}", style=t.s("menu_hint"))
        r.pad_print(line, mode)
        r.blank()

    r.rule("  NAVIGATION  ")
    r.blank()

    nav_text = Text(
        "  Enter numbers (1-9) + Enter to select menu items.\n"
        "  Type q + Enter to go back at any screen.\n"
        "  CODEX automatically adapts to your terminal width.",
        style=t.s("menu_item"),
    )
    r.pad_print(nav_text, mode)
    r.blank()

    r.rule()
    r.blank()

    back = Text()
    back.append("  [q]", style=t.s("menu_key"))
    back.append("  Back to main menu", style=t.s("menu_hint"))
    r.pad_print(back, mode)

    prompt_choice(r, ["q"])
    return {"screen": "home", "args": {}}
