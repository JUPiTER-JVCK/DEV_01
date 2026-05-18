"""CODEX application — main loop and screen router."""

import sys
from pathlib import Path

from .config import Config
from .db import Database
from .renderer import Renderer
from .themes.manager import ThemeManager
from .content.loader import ContentLoader
from .content.search_index import SearchIndex

from .screens import home, topic_list, lesson, settings, search, progress, glossary, help


def main() -> None:
    # Load settings
    cfg = Config.load()

    # Set up theme and renderer
    theme = ThemeManager(cfg.theme)
    r = Renderer(theme)

    # Connect DB and content
    db = Database()
    loader = ContentLoader()

    # Build search index
    index = SearchIndex()
    try:
        all_content = loader.all_lesson_content()
        index.build(all_content)
    except Exception:
        pass  # search degrades gracefully

    # Navigation state
    screen = "home"
    args: dict = {}

    try:
        while True:
            # Sync theme from config (may have changed in settings)
            if theme.name != cfg.theme:
                theme.set_theme(cfg.theme)

            action = _route(r, cfg, db, loader, index, screen, args)
            screen = action.get("screen", "home")
            args = action.get("args", {})

            if screen == "quit":
                break

    except KeyboardInterrupt:
        pass

    # Final cleanup
    db.close()
    cfg.save()

    r.clear()
    r.blank()
    r.pad_print(r.theme.s("subtitle") and "")  # noop
    from rich.text import Text
    farewell = Text("  CODEX — session ended. Knowledge retained.", style=theme.s("muted"))
    r.pad_print(farewell)
    r.blank()


def _route(r: Renderer, cfg: Config, db: Database,
           loader: ContentLoader, index: SearchIndex,
           screen: str, args: dict) -> dict:

    if screen == "home":
        return home.show(r, cfg, db)

    elif screen == "topic_list":
        return topic_list.show_categories(r, cfg, db, loader)

    elif screen == "lesson_list":
        return topic_list.show_lessons(
            r, cfg, db, loader,
            topic_id=args.get("topic_id", ""),
            topic_name=args.get("topic_name", ""),
        )

    elif screen == "lesson":
        return lesson.show(
            r, cfg, db, loader,
            lesson_id=args.get("lesson_id", ""),
            topic_id=args.get("topic_id", ""),
            topic_name=args.get("topic_name", ""),
            lesson_list=args.get("lesson_list"),
        )

    elif screen == "settings":
        result = settings.show(r, cfg)
        # Re-sync theme after settings change
        if theme := r.theme:
            theme.set_theme(cfg.theme)
        return result

    elif screen == "search":
        return search.show(r, cfg, db, loader, index,
                           initial_query=args.get("query", ""))

    elif screen == "progress":
        return progress.show(r, cfg, db, loader)

    elif screen == "glossary":
        return glossary.show(r, cfg, loader)

    elif screen == "help":
        return help.show(r, cfg)

    else:
        return {"screen": "home", "args": {}}
