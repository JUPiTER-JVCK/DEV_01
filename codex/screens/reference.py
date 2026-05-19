"""Command Reference screen — category browser, command list, command detail."""

from rich.text import Text

from ..renderer import Renderer
from ..config import Config
from ..content.loader import ContentLoader
from ..widgets.menu import MenuItem, render_menu, prompt_choice, prompt_input
from ..widgets.info_box import render_info_box


def show(r: Renderer, cfg: Config, loader: ContentLoader) -> dict:
    """Main entry point — loops internally until user exits to home."""
    while True:
        result = _show_categories(r, cfg, loader)
        screen = result.get("screen", "home")
        if screen != "reference":
            return result


def _show_categories(r: Renderer, cfg: Config, loader: ContentLoader) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Reference"], mode)
        r.blank()

    r.rule("COMMAND REFERENCE")
    r.blank()

    sub = Text("  Browse commands by category — syntax, flags, and examples.",
               style=t.s("subtitle"))
    r.pad_print(sub, mode)
    r.blank()

    categories = loader.list_ref_categories()
    items: list[MenuItem] = []
    for i, cat in enumerate(categories, 1):
        items.append(MenuItem(
            str(i),
            cat["name"],
            hint=cat.get("description", ""),
        ))
    items.append(MenuItem("/", "Search commands", hint="find a command by name or keyword"))
    items.append(MenuItem("g", "Glossary",        hint="quick term definitions"))
    items.append(MenuItem("q", "Back",             hint="return to home"))

    render_menu(r, items, compact=(mode == "compact"), mode=mode)
    r.blank()
    r.rule()
    r.blank()

    valid = [str(i) for i in range(1, len(categories) + 1)] + ["/", "g", "q"]
    choice = prompt_choice(r, valid)

    if choice == "q":
        return {"screen": "home", "args": {}}
    if choice == "g":
        return {"screen": "glossary", "args": {}}
    if choice == "/":
        return _search_commands(r, cfg, loader)

    try:
        idx = int(choice) - 1
        cat = categories[idx]
        return _show_command_list(r, cfg, loader, cat["id"], cat["name"])
    except (ValueError, IndexError):
        return {"screen": "reference", "args": {}}


def _show_command_list(r: Renderer, cfg: Config, loader: ContentLoader,
                       category_id: str, category_name: str) -> dict:
    commands = loader.load_ref_category(category_id)

    while True:
        r.clear()
        mode = r.layout_mode(cfg.layout)
        t = r.theme

        if cfg.show_breadcrumbs:
            r.breadcrumb(["CODEX", "Reference", category_name], mode)
            r.blank()

        r.rule(category_name.upper())
        r.blank()

        items: list[MenuItem] = []
        for i, cmd in enumerate(commands, 1):
            desc = cmd.get("description", "")
            items.append(MenuItem(str(i), cmd["name"], hint=desc[:60]))
        items.append(MenuItem("q", "Back", hint="return to categories"))

        render_menu(r, items, compact=(mode == "compact"), mode=mode)
        r.blank()
        r.rule()
        r.blank()

        valid = [str(i) for i in range(1, len(commands) + 1)] + ["q"]
        choice = prompt_choice(r, valid)

        if choice == "q":
            return {"screen": "reference", "args": {}}

        try:
            idx = int(choice) - 1
            _show_command_detail(r, cfg, commands[idx], category_name)
        except (ValueError, IndexError):
            pass


def _show_command_detail(r: Renderer, cfg: Config, cmd: dict,
                         category_name: str) -> None:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme
    cmd_name = cmd.get("name", "")

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Reference", category_name, cmd_name], mode)
        r.blank()

    r.rule()
    r.blank()

    r.pad_print(Text(f"  {cmd_name}", style=t.s("title")), mode)
    r.blank()

    if cmd.get("description"):
        r.pad_print(Text(f"  {cmd['description']}", style=t.s("menu_item"),
                         overflow="fold"), mode)
        r.blank()

    if cmd.get("syntax"):
        render_info_box(r, "standard", cmd["syntax"],
                        title_override="SYNTAX", mode=mode)
        r.blank()

    if cmd.get("flags"):
        r.pad_print(Text("  FLAGS", style=t.s("label")), mode)
        r.blank()
        for f in cmd["flags"]:
            flag_line = Text()
            flag_line.append(f"    {f.get('flag', ''):<22}", style=t.s("accent"))
            flag_line.append(f.get("description", ""), style=t.s("menu_hint"))
            r.pad_print(flag_line, mode)
        r.blank()

    if cmd.get("examples"):
        code_lines: list[str] = []
        for ex in cmd["examples"]:
            if isinstance(ex, dict):
                code_lines.append(ex.get("command", ""))
                if ex.get("description"):
                    code_lines.append(f"  # {ex['description']}")
                code_lines.append("")
            else:
                code_lines.append(str(ex))
        r.code("\n".join(code_lines).strip(), language="bash",
               line_numbers=False, label="Examples", mode=mode)
        r.blank()

    if cmd.get("note"):
        render_info_box(r, "note", cmd["note"], mode=mode)
        r.blank()

    if cmd.get("see_also"):
        see = Text()
        see.append("  See also: ", style=t.s("label"))
        see.append(", ".join(cmd["see_also"]), style=t.s("accent"))
        r.pad_print(see, mode)
        r.blank()

    r.rule()
    r.blank()
    r.pad_print(Text("  Press any key to go back.", style=t.s("menu_hint")), mode)
    r.blank()
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


def _search_commands(r: Renderer, cfg: Config, loader: ContentLoader) -> dict:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Reference", "Search"], mode)
        r.blank()

    r.rule("SEARCH COMMANDS")
    r.blank()
    r.pad_print(Text("  Command name or keyword: ", style=t.s("menu_hint")), mode)

    try:
        query = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return {"screen": "reference", "args": {}}

    if not query:
        return {"screen": "reference", "args": {}}

    results: list[tuple[dict, dict]] = []
    for cat in loader.list_ref_categories():
        for cmd in loader.load_ref_category(cat["id"]):
            searchable = " ".join([
                cmd.get("name", ""),
                cmd.get("description", ""),
                " ".join(f.get("description", "") for f in cmd.get("flags", [])),
                " ".join(str(tag) for tag in cmd.get("tags", [])),
            ]).lower()
            if query in searchable:
                results.append((cat, cmd))

    r.clear()
    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Reference", "Search"], mode)
        r.blank()

    r.rule(f"RESULTS: '{query}'")
    r.blank()

    if not results:
        r.pad_print(Text(f"  No commands found matching '{query}'.",
                         style=t.s("muted")), mode)
        r.blank()
        r.pad_print(Text("  [q] back", style=t.s("menu_hint")), mode)
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        return {"screen": "reference", "args": {}}

    shown = results[:15]
    items: list[MenuItem] = []
    for i, (cat, cmd) in enumerate(shown, 1):
        hint = f"{cat['name']} — {cmd.get('description', '')[:45]}"
        items.append(MenuItem(str(i), cmd["name"], hint=hint))
    items.append(MenuItem("q", "Back"))

    render_menu(r, items, compact=(mode == "compact"), mode=mode)
    r.blank()
    r.rule()
    r.blank()

    valid = [str(i) for i in range(1, len(shown) + 1)] + ["q"]
    choice = prompt_choice(r, valid)

    if choice == "q":
        return {"screen": "reference", "args": {}}

    try:
        idx = int(choice) - 1
        cat, cmd = shown[idx]
        _show_command_detail(r, cfg, cmd, cat["name"])
    except (ValueError, IndexError):
        pass

    return {"screen": "reference", "args": {}}
