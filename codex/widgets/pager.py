"""Simple pager for long content — press Enter to continue, q to stop."""

from rich.text import Text

from ..renderer import Renderer


class Pager:
    """Tracks paging state for long lessons rendered section by section."""

    def __init__(self, r: Renderer, total_sections: int):
        self._r = r
        self._total = total_sections
        self._shown = 0
        self._paused = False

    def section_done(self, idx: int) -> str:
        """Called after rendering a section. Returns 'continue', 'quit', or 'skip'."""
        self._shown = idx + 1
        remaining = self._total - self._shown

        if remaining <= 0:
            return "continue"

        t = self._r.theme
        self._r.blank()
        line = Text()
        line.append(f"  [{self._shown}/{self._total}] ", style=t.s("muted"))
        line.append("Enter", style=t.s("menu_key"))
        line.append(" next  ", style=t.s("menu_hint"))
        line.append("s", style=t.s("menu_key"))
        line.append(" skip all  ", style=t.s("menu_hint"))
        line.append("q", style=t.s("menu_key"))
        line.append(" back", style=t.s("menu_hint"))
        self._r.pad_print(line)

        try:
            raw = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"

        if raw == "q":
            return "quit"
        if raw == "s":
            return "skip"
        return "continue"

    def end_prompt(self, lesson_id: str = "", next_id: str = "",
                   bookmarked: bool = False) -> str:
        """Final prompt after all sections. Returns action key."""
        t = self._r.theme
        self._r.blank()
        self._r.rule("  End of Lesson  ")
        self._r.blank()

        line = Text()
        line.append("  ", style="")
        line.append("b", style=t.s("menu_key"))
        line.append(" bookmark  ", style=t.s("menu_hint"))
        line.append("n", style=t.s("menu_key"))
        line.append(" add note  ", style=t.s("menu_hint"))
        if next_id:
            line.append("Enter", style=t.s("menu_key"))
            line.append(" next lesson  ", style=t.s("menu_hint"))
        line.append("q", style=t.s("menu_key"))
        line.append(" back", style=t.s("menu_hint"))

        if bookmarked:
            line.append("  [bookmarked]", style=t.s("accent"))

        self._r.pad_print(line)

        try:
            raw = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "q"

        return raw if raw else ("next" if next_id else "q")
