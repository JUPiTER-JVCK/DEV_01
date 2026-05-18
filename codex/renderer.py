"""Central rendering layer — wraps Rich Console with theme-aware helpers."""

import shutil
from rich.console import Console
from rich.style import Style
from rich.text import Text
from rich.rule import Rule
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.padding import Padding
from rich.align import Align
from rich import box

from .themes.manager import ThemeManager


class Renderer:
    def __init__(self, theme: ThemeManager):
        self.theme = theme
        self._console = Console(highlight=False, markup=True)

    @property
    def console(self) -> Console:
        return self._console

    def width(self) -> int:
        return self._console.width or shutil.get_terminal_size().columns

    def height(self) -> int:
        return self._console.height or shutil.get_terminal_size().lines

    def layout_mode(self, override: str = "auto") -> str:
        if override != "auto":
            return override
        w = self.width()
        if w < 80:
            return "compact"
        elif w < 120:
            return "standard"
        return "wide"

    def content_width(self, mode: str = "auto") -> int:
        w = self.width()
        m = self.layout_mode(mode)
        if m == "compact":
            return w - 2
        elif m == "standard":
            return min(w - 4, 96)
        return min(w - 8, 120)

    def margin(self, mode: str = "auto") -> int:
        w = self.width()
        cw = self.content_width(mode)
        return max(0, (w - cw) // 2)

    def print(self, *args, **kwargs):
        self._console.print(*args, **kwargs)

    def clear(self):
        self._console.clear()

    def rule(self, title: str = "", style: str | None = None):
        s = style or self.theme.s("header_rule")
        self._console.print(Rule(title, style=s))

    def pad_print(self, renderable, mode: str = "auto"):
        m = self.margin(mode)
        if m > 0:
            self._console.print(Padding(renderable, pad=(0, m)))
        else:
            self._console.print(renderable)

    def title(self, text: str, mode: str = "auto"):
        t = Text(text, style=self.theme.s("title"))
        self.pad_print(t, mode)

    def subtitle(self, text: str, mode: str = "auto"):
        t = Text(text, style=self.theme.s("subtitle"))
        self.pad_print(t, mode)

    def muted(self, text: str, mode: str = "auto"):
        t = Text(text, style=self.theme.s("muted"))
        self.pad_print(t, mode)

    def success(self, text: str):
        self._console.print(f"[{self.theme.s('success')}]{text}[/]")

    def error(self, text: str):
        self._console.print(f"[{self.theme.s('error')}]{text}[/]")

    def info(self, text: str):
        self._console.print(f"[{self.theme.s('info')}]{text}[/]")

    def warning(self, text: str):
        self._console.print(f"[{self.theme.s('warning')}]{text}[/]")

    def blank(self, n: int = 1):
        for _ in range(n):
            self._console.print()

    def panel(self, content, title: str = "", border_style: str | None = None,
              padding: tuple = (0, 1), mode: str = "auto") -> Panel:
        bs = border_style or self.theme.s("panel_border")
        p = Panel(content, title=title, border_style=bs, padding=padding,
                  box=box.ROUNDED)
        self.pad_print(p, mode)
        return p

    def code(self, source: str, language: str = "python",
             line_numbers: bool = True, label: str = "", mode: str = "auto"):
        syn = Syntax(
            source.rstrip(),
            language,
            theme=self.theme.syntax_theme(),
            line_numbers=line_numbers,
            word_wrap=True,
        )
        title = f" {label} " if label else ""
        bs = self.theme.s("panel_border")
        p = Panel(syn, title=title, title_align="left",
                  border_style=bs, box=box.ROUNDED, padding=(0, 1))
        self.pad_print(p, mode)

    def breadcrumb(self, parts: list[str], mode: str = "auto"):
        if not parts:
            return
        bc = self.theme.s("breadcrumb")
        sep = f"[{bc}] > [/]"
        crumbs = sep.join(f"[{bc}]{p}[/]" for p in parts)
        self._console.print(f"[{bc}]  {crumbs}[/]")

    def progress_bar(self, done: int, total: int, width: int = 20,
                     label: str = "") -> str:
        if total == 0:
            return ""
        pct = done / total
        filled = int(pct * width)
        bar_s = self.theme.s("progress_bar")
        bg_s = self.theme.s("progress_bg")
        bar = f"[{bar_s}]{'█' * filled}[/][{bg_s}]{'░' * (width - filled)}[/]"
        pct_str = f"{int(pct * 100):3d}%"
        lbl = f" {label}" if label else ""
        return f"{bar} {pct_str}{lbl}"

    def hr(self, mode: str = "auto"):
        w = self.content_width(mode)
        m = self.margin(mode)
        line = " " * m + self.theme.s("header_rule") and "─" * w
        self._console.print(f"[{self.theme.s('header_rule')}]{'─' * w}[/]")
