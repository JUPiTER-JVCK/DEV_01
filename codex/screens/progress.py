"""Progress screen — completed lessons, bookmarks, and personal notes."""

from rich.text import Text
from rich.table import Table
from rich import box as rbox

from ..renderer import Renderer
from ..config import Config
from ..db import Database
from ..content.loader import ContentLoader
from ..widgets.menu import prompt_choice


def show(r: Renderer, cfg: Config, db: Database, loader: ContentLoader) -> dict:
    while True:
        result = _progress_menu(r, cfg, db, loader)
        if result.get("screen") != "progress":
            return result


def _progress_menu(r: Renderer, cfg: Config, db: Database,
                   loader: ContentLoader) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Progress"], mode)
        r.blank()

    r.rule("  PROGRESS  ")
    r.blank()

    all_lessons = loader.all_lessons()
    completed_ids = db.completed_ids()
    total = len(all_lessons)
    done = len(completed_ids)

    pct = int((done / total) * 100) if total > 0 else 0
    prog = r.progress_bar(done, total, width=24, label=f"  {done}/{total} lessons")

    if cfg.show_progress_bar and prog:
        r.pad_print(Text(f"  {prog}", style=""), mode)
        r.blank()

    summary_line = Text()
    summary_line.append("  Overall: ", style=t.s("muted"))
    summary_line.append(f"{pct}% complete", style=t.s("accent"))
    r.pad_print(summary_line, mode)
    r.blank()

    # Per-topic breakdown
    topics = loader.list_topics()
    if topics:
        table = Table(box=None, show_header=True, padding=(0, 2),
                      header_style=t.s("muted"))
        table.add_column("Topic", style=t.s("menu_item"))
        table.add_column("Done", style=t.s("success"), justify="right")
        table.add_column("Total", style=t.s("muted"), justify="right")
        table.add_column("", style=t.s("dim"))

        for topic in topics:
            lessons = loader.list_lessons(topic["id"])
            t_total = len(lessons)
            t_done = sum(1 for l in lessons if l["id"] in completed_ids)
            t_pct = int((t_done / t_total) * 100) if t_total > 0 else 0
            bar = ("█" * (t_pct // 10)) + ("░" * (10 - t_pct // 10))
            table.add_row(topic["name"], str(t_done), str(t_total), bar)

        r.pad_print(table, mode)
        r.blank()

    r.rule()
    r.blank()

    items_line = Text()
    items_line.append("  [1]", style=t.s("menu_number"))
    items_line.append("  Bookmarks", style=t.s("menu_item"))
    items_line.append(f"  — {len(db.get_bookmarks())} saved", style=t.s("menu_hint"))
    r.pad_print(items_line, mode)
    r.blank()

    notes_line = Text()
    notes_line.append("  [2]", style=t.s("menu_number"))
    notes_line.append("  My Notes", style=t.s("menu_item"))
    notes_line.append(f"  — {len(db.get_all_notes())} notes", style=t.s("menu_hint"))
    r.pad_print(notes_line, mode)
    r.blank()

    back_line = Text()
    back_line.append("  [q]", style=t.s("menu_number"))
    back_line.append("  Back", style=t.s("menu_item"))
    r.pad_print(back_line, mode)
    r.blank()
    r.rule()
    r.blank()

    choice = prompt_choice(r, ["1", "2", "q"])

    if choice == "1":
        return _show_bookmarks(r, cfg, db, loader)
    if choice == "2":
        return _show_notes(r, cfg, db)
    return {"screen": "home", "args": {}}


def _show_bookmarks(r: Renderer, cfg: Config, db: Database,
                    loader: ContentLoader) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    r.rule("  BOOKMARKS  ")
    r.blank()

    bookmarks = db.get_bookmarks()
    if not bookmarks:
        r.pad_print(Text("  No bookmarks yet. Press [b] in any lesson.", style=t.s("muted")), mode)
        r.blank()
        r.pad_print(Text("  [q] Back", style=t.s("menu_hint")), mode)
        prompt_choice(r, ["q"])
        return {"screen": "progress", "args": {}}

    for i, bm in enumerate(bookmarks, 1):
        line = Text()
        line.append(f"  [{i:2d}]", style=t.s("menu_number"))
        line.append(f"  {bm['lesson_title']}", style=t.s("menu_item"))
        line.append(f"  — {bm['saved_at'][:10]}", style=t.s("dim"))
        r.pad_print(line, mode)
        if not cfg.compact_menus:
            r.blank()

    r.blank()
    r.rule()
    r.blank()
    hint = Text()
    hint.append("  Number to open  ", style=t.s("menu_hint"))
    hint.append("[q]", style=t.s("menu_key"))
    hint.append(" back", style=t.s("menu_hint"))
    r.pad_print(hint, mode)

    valid = [str(i) for i in range(1, len(bookmarks) + 1)] + ["q"]
    choice = prompt_choice(r, valid)

    if choice == "q":
        return {"screen": "progress", "args": {}}

    try:
        bm = bookmarks[int(choice) - 1]
        for topic in loader.list_topics():
            lessons = loader.list_lessons(topic["id"])
            for lesson in lessons:
                if lesson["id"] == bm["lesson_id"]:
                    return {
                        "screen": "lesson",
                        "args": {
                            "lesson_id":   bm["lesson_id"],
                            "topic_id":    topic["id"],
                            "topic_name":  topic["name"],
                            "lesson_list": lessons,
                        },
                    }
    except (ValueError, IndexError):
        pass

    return {"screen": "progress", "args": {}}


def _show_notes(r: Renderer, cfg: Config, db: Database) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    r.rule("  MY NOTES  ")
    r.blank()

    notes = db.get_all_notes()
    if not notes:
        r.pad_print(Text("  No notes yet. Press [n] in any lesson.", style=t.s("muted")), mode)
        r.blank()
    else:
        for note in notes:
            date_line = Text()
            date_line.append(f"  {note['created_at'][:16]}  ", style=t.s("dim"))
            date_line.append(f"{note['lesson_id']}", style=t.s("muted"))
            r.pad_print(date_line, mode)

            note_line = Text(f"    {note['content']}", style=t.s("menu_item"), overflow="fold")
            r.pad_print(note_line, mode)
            r.blank()

    r.rule()
    r.blank()
    r.pad_print(Text("  [q] Back", style=t.s("menu_hint")), mode)
    prompt_choice(r, ["q"])
    return {"screen": "progress", "args": {}}
