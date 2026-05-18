"""Topic browser — categories and lesson lists."""

from rich.text import Text

from ..renderer import Renderer
from ..config import Config
from ..db import Database
from ..content.loader import ContentLoader
from ..widgets.art import get_topic_art
from ..widgets.menu import MenuItem, render_menu, prompt_choice


def show_categories(r: Renderer, cfg: Config, db: Database,
                    loader: ContentLoader) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Learn"], mode)
        r.blank()

    r.rule("  LEARN  ")
    r.blank()

    title = Text("  Choose a topic to explore", style=t.s("subtitle"))
    r.pad_print(title, mode)
    r.blank()

    topics = loader.list_topics()
    completed = db.completed_ids()

    items = []
    for i, topic in enumerate(topics, 1):
        total = loader.lesson_count(topic["id"])
        done = sum(1 for l in loader.list_lessons(topic["id"])
                   if l["id"] in completed)
        badge = f"{done}/{total}" if total > 0 else ""
        items.append(MenuItem(str(i), topic["name"],
                              hint=topic.get("description", ""),
                              badge=badge))

    items.append(MenuItem("q", "Back", hint="return to main menu"))

    render_menu(r, items, compact=(mode == "compact"), mode=mode)
    r.blank()
    r.rule()
    r.blank()

    valid = [str(i) for i in range(1, len(topics) + 1)] + ["q"]
    choice = prompt_choice(r, valid)

    if choice == "q":
        return {"screen": "home", "args": {}}

    try:
        idx = int(choice) - 1
        topic = topics[idx]
    except (ValueError, IndexError):
        return {"screen": "topic_list", "args": {}}

    return {"screen": "lesson_list", "args": {"topic_id": topic["id"],
                                               "topic_name": topic["name"]}}


def show_lessons(r: Renderer, cfg: Config, db: Database,
                 loader: ContentLoader, topic_id: str,
                 topic_name: str) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Learn", topic_name], mode)
        r.blank()

    if cfg.ascii_art_headers and mode != "compact":
        art = get_topic_art(topic_id)
        r.pad_print(Text(art, style=t.s("muted")), mode)
    else:
        r.rule(f"  {topic_name.upper()}  ")
        r.blank()

    lessons = loader.list_lessons(topic_id)
    completed = db.completed_ids()

    items = []
    for i, lesson in enumerate(lessons, 1):
        done = lesson["id"] in completed
        badge = "[+]" if done and cfg.highlight_on_completion else ""
        hint = lesson.get("subtitle", "")
        diff = lesson.get("difficulty", "")
        if diff:
            hint = f"{diff}  {hint}" if hint else diff
        mins = lesson.get("estimated_minutes", 0)
        if mins:
            hint = f"{hint}  ~{mins}m" if hint else f"~{mins}m"
        items.append(MenuItem(str(i), lesson["title"],
                              hint=hint, badge=badge))

    items.append(MenuItem("q", "Back", hint="return to topics"))

    render_menu(r, items, compact=(mode == "compact"), mode=mode)
    r.blank()
    r.rule()
    r.blank()

    valid = [str(i) for i in range(1, len(lessons) + 1)] + ["q"]
    choice = prompt_choice(r, valid)

    if choice == "q":
        return {"screen": "topic_list", "args": {}}

    try:
        idx = int(choice) - 1
        lesson = lessons[idx]
    except (ValueError, IndexError):
        return {"screen": "lesson_list",
                "args": {"topic_id": topic_id, "topic_name": topic_name}}

    return {"screen": "lesson",
            "args": {
                "lesson_id": lesson["id"],
                "topic_id":  topic_id,
                "topic_name": topic_name,
                "lesson_list": lessons,
            }}
