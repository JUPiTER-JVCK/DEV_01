"""Search screen — full-text search across all CODEX content."""

from rich.text import Text

from ..renderer import Renderer
from ..config import Config
from ..db import Database
from ..content.loader import ContentLoader
from ..content.search_index import SearchIndex
from ..widgets.menu import prompt_input, prompt_choice


def show(r: Renderer, cfg: Config, db: Database,
         loader: ContentLoader, index: SearchIndex,
         initial_query: str = "") -> dict:
    while True:
        result = _search_loop(r, cfg, db, loader, index, initial_query)
        if result.get("screen") != "search":
            return result
        initial_query = ""


def _search_loop(r: Renderer, cfg: Config, db: Database,
                 loader: ContentLoader, index: SearchIndex,
                 initial_query: str = "") -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Search"], mode)
        r.blank()

    r.rule("  SEARCH  ")
    r.blank()

    sub = Text("  Search lessons, definitions, and examples", style=t.s("subtitle"))
    r.pad_print(sub, mode)
    r.blank()

    query = initial_query or prompt_input(r, "Search", "")
    if not query:
        return {"screen": "home", "args": {}}

    r.blank()
    r.rule(f"  Results for \"{query}\"  ")
    r.blank()

    results = index.search(query, limit=15)

    if not results:
        no_results = Text(f"  No results found for \"{query}\"", style=t.s("warning"))
        r.pad_print(no_results, mode)
        r.blank()
        again = prompt_choice(r, ["s", "q"], "Search again [s] or back [q]")
        if again == "s":
            return {"screen": "search", "args": {}}
        return {"screen": "home", "args": {}}

    for i, result in enumerate(results, 1):
        line = Text()
        line.append(f"  [{i:2d}]", style=t.s("menu_number"))
        line.append(f"  {result['lesson_title']}", style=t.s("menu_item"))
        line.append(f"  — {result['topic_name']}", style=t.s("menu_hint"))
        if result.get("excerpt"):
            r.pad_print(line, mode)
            excerpt = Text()
            excerpt.append(f"        {result['excerpt'][:80]}...",
                           style=t.s("dim"))
            r.pad_print(excerpt, mode)
        else:
            r.pad_print(line, mode)

        if not cfg.compact_menus:
            r.blank()

    r.rule()
    r.blank()

    line = Text()
    line.append("  Enter number to open  ", style=t.s("menu_hint"))
    line.append("[s]", style=t.s("menu_key"))
    line.append(" search again  ", style=t.s("menu_hint"))
    line.append("[q]", style=t.s("menu_key"))
    line.append(" back", style=t.s("menu_hint"))
    r.pad_print(line, mode)

    valid = [str(i) for i in range(1, len(results) + 1)] + ["s", "q"]
    choice = prompt_choice(r, valid, "Open")

    if choice == "q":
        return {"screen": "home", "args": {}}
    if choice == "s":
        return {"screen": "search", "args": {}}

    try:
        idx = int(choice) - 1
        result = results[idx]
        lessons = loader.list_lessons(result["topic_id"])
        return {
            "screen": "lesson",
            "args": {
                "lesson_id":   result["lesson_id"],
                "topic_id":    result["topic_id"],
                "topic_name":  result["topic_name"],
                "lesson_list": lessons,
            },
        }
    except (ValueError, IndexError):
        return {"screen": "search", "args": {}}
