"""Home screen — CODEX banner, main menu."""

from rich.text import Text
from rich.align import Align

from ..renderer import Renderer
from ..config import Config
from ..db import Database
from ..widgets.art import get_banner, CODEX_TAGLINE
from ..widgets.menu import MenuItem, render_menu, render_key_hints, prompt_choice


def show(r: Renderer, cfg: Config, db: Database) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    # Banner
    banner = get_banner(wide=(mode != "compact"))
    banner_text = Text(banner, style=t.s("accent"))
    r.pad_print(Align.center(banner_text) if mode == "wide" else banner_text, mode)

    tagline = Text(f"  {CODEX_TAGLINE}", style=t.s("subtitle"))
    r.pad_print(tagline, mode)
    r.blank()

    # Progress summary
    done = db.completed_count()
    if done > 0:
        prog_line = Text()
        prog_line.append("  Progress: ", style=t.s("muted"))
        prog_line.append(f"{done} lesson(s) completed", style=t.s("accent"))
        r.pad_print(prog_line, mode)
        r.blank()

    r.rule()
    r.blank()

    items = [
        MenuItem("1", "Learn",     hint="topics, lessons, and examples"),
        MenuItem("2", "Reference", hint="glossary and quick lookups"),
        MenuItem("3", "Search",    hint="find anything across all content"),
        MenuItem("4", "Progress",  hint="your history, bookmarks, and notes"),
        MenuItem("5", "Settings",  hint="themes, layout, and display"),
        MenuItem("?", "Help",      hint="keyboard shortcuts and about"),
        MenuItem("q", "Quit",      hint="exit CODEX"),
    ]

    render_menu(r, items, compact=(mode == "compact"), mode=mode)
    r.blank()
    r.rule()
    r.blank()

    choice = prompt_choice(r, ["1", "2", "3", "4", "5", "?", "q"])

    mapping = {
        "1": {"screen": "topic_list", "args": {}},
        "2": {"screen": "glossary",   "args": {}},
        "3": {"screen": "search",     "args": {}},
        "4": {"screen": "progress",   "args": {}},
        "5": {"screen": "settings",   "args": {}},
        "?": {"screen": "help",       "args": {}},
        "q": {"screen": "quit",       "args": {}},
    }
    return mapping.get(choice, {"screen": "home", "args": {}})
