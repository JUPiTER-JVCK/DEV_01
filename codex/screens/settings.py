"""Settings screen — browse and edit all CODEX preferences."""

from rich.text import Text

from ..renderer import Renderer
from ..config import Config, SETTINGS_META
from ..themes.manager import ThemeManager
from ..themes.definitions import THEMES
from ..widgets.menu import MenuItem, render_menu, prompt_choice, prompt_input


def show(r: Renderer, cfg: Config) -> dict:
    while True:
        result = _settings_menu(r, cfg)
        if result == "back":
            cfg.save()
            return {"screen": "home", "args": {}}


def _settings_menu(r: Renderer, cfg: Config) -> str:
    r.clear()
    mode = r.layout_mode(cfg.layout)
    t = r.theme

    if cfg.show_breadcrumbs:
        r.breadcrumb(["CODEX", "Settings"], mode)
        r.blank()

    r.rule("  SETTINGS  ")
    r.blank()

    sub = Text("  Customize your CODEX experience", style=t.s("subtitle"))
    r.pad_print(sub, mode)
    r.blank()

    groups: dict[str, list] = {}
    for key, meta in SETTINGS_META.items():
        grp = meta.get("group", "Other")
        groups.setdefault(grp, []).append((key, meta))

    items = []
    idx = 1
    key_map = {}
    for grp_name, settings in groups.items():
        grp_label = Text(f"  ── {grp_name} ", style=t.s("muted"))
        r.pad_print(grp_label, mode)
        r.blank()

        for key, meta in settings:
            val = cfg.get(key)
            val_str = _format_value(val, meta)
            hint = f"{val_str}"
            if meta.get("hint"):
                hint += f"  ({meta['hint']})"
            items.append(MenuItem(str(idx), meta["label"], hint=hint))
            key_map[str(idx)] = key
            idx += 1

        r.blank()

    for item in items:
        line = Text()
        line.append(f"  [{item.key}]", style=t.s("menu_number"))
        line.append(f"  {item.label:<28}", style=t.s("menu_item"))
        line.append(f"  {item.hint}", style=t.s("menu_hint"))
        r.pad_print(line, mode)

    r.blank()
    r.rule()
    r.blank()

    line = Text()
    line.append("  Enter number to change setting  ", style=t.s("menu_hint"))
    line.append("[q]", style=t.s("menu_key"))
    line.append(" back", style=t.s("menu_hint"))
    r.pad_print(line, mode)
    r.blank()

    valid = [str(i) for i in range(1, idx)] + ["q"]
    choice = prompt_choice(r, valid, "Setting")

    if choice == "q":
        return "back"

    if choice in key_map:
        key = key_map[choice]
        _edit_setting(r, cfg, key, SETTINGS_META[key], mode)

    return "continue"


def _format_value(val, meta: dict) -> str:
    if meta["type"] == "bool":
        return "ON" if val else "off"
    return str(val)


def _edit_setting(r: Renderer, cfg: Config, key: str, meta: dict,
                  mode: str) -> None:
    t = r.theme
    r.blank()
    current = cfg.get(key)

    r.pad_print(Text(f"  Editing: {meta['label']}", style=t.s("title")), mode)
    r.pad_print(Text(f"  Current: {_format_value(current, meta)}", style=t.s("muted")), mode)
    r.blank()

    if meta["type"] == "bool":
        new_val = not current
        cfg.set(key, new_val)
        r.success(f"  Set to: {'ON' if new_val else 'off'}")

        if key == "theme":
            pass

    elif meta["type"] == "choice":
        choices = meta["choices"]
        for i, c in enumerate(choices, 1):
            marker = " <" if c == current else ""
            info_line = Text()
            info_line.append(f"  [{i}]", style=t.s("menu_number"))
            info_line.append(f"  {c}", style=t.s("menu_item"))
            if key == "theme" and c in THEMES:
                info_line.append(f"  — {THEMES[c].get('description', '')}", style=t.s("dim"))
            info_line.append(marker, style=t.s("accent"))
            r.pad_print(info_line, mode)

        r.blank()
        valid = [str(i) for i in range(1, len(choices) + 1)] + ["q"]
        choice = prompt_choice(r, valid, "Select")
        if choice != "q":
            try:
                new_val = choices[int(choice) - 1]
                cfg.set(key, new_val)
                r.success(f"  Set to: {new_val}")
                if key == "theme":
                    r.theme.set_theme(new_val)
            except (ValueError, IndexError):
                pass

    elif meta["type"] == "int":
        mn = meta.get("min", 1)
        mx = meta.get("max", 100)
        raw = prompt_input(r, f"Enter value ({mn}-{mx})", str(current))
        try:
            new_val = int(raw)
            if mn <= new_val <= mx:
                cfg.set(key, new_val)
                r.success(f"  Set to: {new_val}")
            else:
                r.error(f"  Value must be between {mn} and {mx}")
        except ValueError:
            r.error("  Invalid number")

    import time
    time.sleep(0.6)
