"""Lesson viewer — renders all section types, handles bookmarks and notes."""

import time
from rich.text import Text
from rich.rule import Rule
from rich.console import Group

from ..renderer import Renderer
from ..config import Config
from ..db import Database
from ..content.loader import ContentLoader
from ..widgets.art import get_difficulty_badge, section_divider, COMPLETION_ART
from ..widgets.pager import Pager
from ..widgets.menu import prompt_input
from ..widgets.info_box import (
    render_info_box, render_formula_box, render_analogy,
    render_interactive,
)


def show(r: Renderer, cfg: Config, db: Database, loader: ContentLoader,
         lesson_id: str, topic_id: str, topic_name: str,
         lesson_list: list | None = None) -> dict:

    lesson = loader.load_lesson(topic_id, lesson_id)
    if not lesson:
        r.error(f"  Lesson not found: {lesson_id}")
        input()
        return {"screen": "lesson_list",
                "args": {"topic_id": topic_id, "topic_name": topic_name}}

    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    lesson_list = lesson_list or []
    lesson_ids = [l["id"] for l in lesson_list]
    current_idx = lesson_ids.index(lesson_id) if lesson_id in lesson_ids else -1
    next_id = lesson_ids[current_idx + 1] if current_idx >= 0 and current_idx + 1 < len(lesson_ids) else ""
    prev_id = lesson_ids[current_idx - 1] if current_idx > 0 else ""

    bookmarked = db.is_bookmarked(lesson_id)
    completed = db.is_complete(lesson_id)
    start_time = time.time()

    # Header
    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Learn", topic_name, lesson["title"]], mode)
        r.blank()

    r.rule()
    r.blank()

    header = Text()
    header.append(f"  {lesson['title']}", style=t.s("title"))
    r.pad_print(header, mode)

    if lesson.get("subtitle"):
        sub = Text()
        sub.append(f"  {lesson['subtitle']}", style=t.s("subtitle"))
        r.pad_print(sub, mode)

    r.blank()

    # Metadata row
    meta = Text("  ")
    if lesson.get("difficulty"):
        badge = get_difficulty_badge(lesson["difficulty"])
        meta.append(badge, style=t.s("muted"))
        meta.append("  ", style="")
    if lesson.get("estimated_minutes"):
        meta.append(f"~{lesson['estimated_minutes']} min", style=t.s("muted"))
        meta.append("  ", style="")
    if lesson.get("tags"):
        tags = "  ".join(f"#{tag}" for tag in lesson["tags"][:4])
        meta.append(tags, style=t.s("tag"))
    if completed:
        meta.append("  [completed]", style=t.s("success"))
    if bookmarked:
        meta.append("  [bookmarked]", style=t.s("accent"))
    if str(meta).strip():
        r.pad_print(meta, mode)
        r.blank()

    r.rule()
    r.blank()

    # Render sections
    sections = lesson.get("sections", [])
    pager = Pager(r, len(sections))
    action = "continue"

    for idx, section in enumerate(sections):
        if action == "skip":
            break

        _render_section(r, cfg, section, mode)
        r.blank()

        if idx < len(sections) - 1:
            action = pager.section_done(idx)
            if action == "quit":
                return {"screen": "lesson_list",
                        "args": {"topic_id": topic_id, "topic_name": topic_name}}
            if action != "skip":
                r.clear()
                if cfg.show_breadcrumbs:
                    r.breadcrumb(["CODEX", "Learn", topic_name, lesson["title"]], mode)
                    r.blank()

    # Mark complete
    elapsed = int(time.time() - start_time)
    db.mark_complete(lesson_id, elapsed)

    # Completion art
    if cfg.show_word_art:
        r.blank()
        r.pad_print(Text(COMPLETION_ART, style=t.s("success")), mode)

    # End prompt
    final = pager.end_prompt(lesson_id, next_id, bookmarked)

    if final == "b":
        db.add_bookmark(lesson_id, lesson["title"])
        r.success("  Bookmarked!")
        time.sleep(0.8)
        return {"screen": "lesson",
                "args": {"lesson_id": lesson_id, "topic_id": topic_id,
                         "topic_name": topic_name, "lesson_list": lesson_list}}

    if final == "n":
        note = prompt_input(r, "Your note")
        if note:
            db.add_note(lesson_id, note)
            r.success("  Note saved.")
            time.sleep(0.8)
        return {"screen": "lesson",
                "args": {"lesson_id": lesson_id, "topic_id": topic_id,
                         "topic_name": topic_name, "lesson_list": lesson_list}}

    if (final == "" or final == "next") and next_id:
        return {"screen": "lesson",
                "args": {"lesson_id": next_id, "topic_id": topic_id,
                         "topic_name": topic_name, "lesson_list": lesson_list}}

    return {"screen": "lesson_list",
            "args": {"topic_id": topic_id, "topic_name": topic_name}}


def _render_section(r: Renderer, cfg: Config, section: dict,
                    mode: str) -> None:
    s_type = section.get("type", "text")
    t = r.theme

    if s_type == "text":
        content = section.get("content", "")
        for line in content.strip().splitlines():
            line = line.strip()
            if line:
                txt = Text(f"  {line}", style=t.s("menu_item"), overflow="fold")
                r.pad_print(txt, mode)
            else:
                r.blank()

    elif s_type == "code":
        if cfg.line_numbers or True:
            r.code(
                section.get("code", ""),
                language=section.get("language", "text"),
                line_numbers=cfg.line_numbers,
                label=section.get("label", ""),
                mode=mode,
            )

    elif s_type == "formula":
        render_formula_box(
            r,
            section.get("formula", ""),
            section.get("variables", {}),
            label=section.get("label", ""),
            mode=mode,
        )

    elif s_type == "analogy":
        render_analogy(r, section.get("title", "Analogy"),
                       section.get("items", []), mode)

    elif s_type in ("fact", "note", "warning", "tip", "history",
                    "definition", "standard", "example"):
        if cfg.show_facts or s_type not in ("fact", "tip"):
            render_info_box(r, s_type, section.get("content", ""),
                            title_override=section.get("title", ""),
                            mode=mode)

    elif s_type == "interactive":
        render_interactive(
            r,
            section.get("prompt", ""),
            section.get("answer", ""),
            section.get("hint", ""),
            mode,
        )

    elif s_type == "ascii_diagram":
        art_text = Text(section.get("art", ""), style=t.s("muted"))
        if section.get("label"):
            r.pad_print(Text(f"  {section['label']}", style=t.s("label")), mode)
        r.pad_print(art_text, mode)

    elif s_type == "list":
        title = section.get("title", "")
        if title:
            r.pad_print(Text(f"  {title}", style=t.s("label")), mode)
            r.blank()
        for item in section.get("items", []):
            line = Text()
            line.append("    - ", style=t.s("accent"))
            line.append(item, style=t.s("menu_item"))
            r.pad_print(line, mode)

    elif s_type == "divider":
        r.blank()
        style = section.get("style", 0)
        r.pad_print(Text(section_divider(style), style=t.s("muted")), mode)
        r.blank()

    elif s_type == "heading":
        r.blank()
        heading = Text(f"  {section.get('text', '')}", style=t.s("title"))
        r.pad_print(heading, mode)
        r.blank()
