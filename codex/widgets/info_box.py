"""Info box widgets — fact, note, warning, tip, formula, interactive callouts."""

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box as rbox

from ..renderer import Renderer

BOX_TYPES = {
    "fact":        ("[*] DID YOU KNOW",  "box_fact"),
    "note":        ("[i] NOTE",          "box_note"),
    "warning":     ("[!] WARNING",       "box_warning"),
    "tip":         ("[>] TIP",           "box_tip"),
    "formula":     ("[=] FORMULA",       "box_formula"),
    "interactive": ("[?] TRY IT",        "box_interactive"),
    "art":         ("    ",              "box_art"),
    "analogy":     ("[~] ANALOGY",       "box_note"),
    "history":     ("[H] HISTORY",       "box_fact"),
    "example":     ("[>] EXAMPLE",       "box_tip"),
    "definition":  ("[D] DEFINITION",    "box_note"),
    "standard":    ("[S] STANDARD",      "box_formula"),
}


def render_info_box(r: Renderer, box_type: str, content: str,
                    title_override: str = "", mode: str = "auto") -> None:
    t = r.theme
    default_title, color_key = BOX_TYPES.get(box_type, ("[i] INFO", "box_note"))
    title = title_override or default_title
    color = t.s(color_key)

    body = Text(content, style=t.s("menu_item"), overflow="fold")
    p = Panel(
        body,
        title=f"[{color}]{title}[/]",
        title_align="left",
        border_style=color,
        box=rbox.ROUNDED,
        padding=(0, 2),
    )
    r.pad_print(p, mode)


def render_formula_box(r: Renderer, formula: str, variables: dict[str, str],
                       label: str = "", mode: str = "auto") -> None:
    t = r.theme
    color = t.s("box_formula")
    title = f"[{color}][=] {label or 'FORMULA'}[/]"

    lines: list[Text] = []

    formula_line = Text()
    formula_line.append(f"  {formula}", style=t.s("formula"))
    lines.append(formula_line)

    if variables:
        lines.append(Text())
        for var, desc in variables.items():
            vl = Text()
            vl.append(f"  {var}", style=t.s("accent"))
            vl.append(f"  =  {desc}", style=t.s("menu_hint"))
            lines.append(vl)

    from rich.console import Group
    body = Group(*lines)
    p = Panel(body, title=title, title_align="left",
              border_style=color, box=rbox.ROUNDED, padding=(0, 1))
    r.pad_print(p, mode)


def render_analogy(r: Renderer, title: str, items: list[str],
                   mode: str = "auto") -> None:
    t = r.theme
    color = t.s("box_note")
    lines: list[Text] = []
    for item in items:
        line = Text()
        line.append("  - ", style=t.s("accent"))
        line.append(item, style=t.s("menu_item"))
        lines.append(line)

    from rich.console import Group
    body = Group(*lines)
    box_title = f"[{color}][~] {title}[/]"
    p = Panel(body, title=box_title, title_align="left",
              border_style=color, box=rbox.ROUNDED, padding=(0, 1))
    r.pad_print(p, mode)


def render_variables_table(r: Renderer, variables: dict[str, str],
                           mode: str = "auto") -> None:
    t = r.theme
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column("var", style=t.s("accent"), no_wrap=True)
    table.add_column("desc", style=t.s("menu_item"))
    for var, desc in variables.items():
        table.add_row(var, desc)
    r.pad_print(table, mode)


def render_interactive(r: Renderer, prompt: str, answer: str,
                       hint: str = "", mode: str = "auto") -> bool:
    """Render an interactive quiz prompt. Returns True if answered."""
    t = r.theme
    color = t.s("box_interactive")

    render_info_box(r, "interactive", prompt, mode=mode)
    r.blank()

    line = Text()
    line.append("  Your answer (Enter to reveal): ", style=t.s("menu_hint"))
    r.pad_print(line, mode)

    try:
        user_ans = input().strip()
    except (EOFError, KeyboardInterrupt):
        user_ans = ""

    r.blank()

    if user_ans:
        correct = user_ans.lower().replace(" ", "") in answer.lower().replace(" ", "")
        if correct:
            r.success("  Correct!")
        else:
            r.warning("  Not quite — here's the answer:")

    ans_line = Text()
    ans_line.append("  Answer: ", style=t.s("label"))
    ans_line.append(answer, style=t.s("success"))
    r.pad_print(ans_line, mode)

    if hint:
        r.blank()
        hint_line = Text()
        hint_line.append("  Hint: ", style=t.s("menu_hint"))
        hint_line.append(hint, style=t.s("dim"))
        r.pad_print(hint_line, mode)

    return True
