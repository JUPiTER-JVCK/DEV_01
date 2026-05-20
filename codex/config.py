"""Settings management — load, save, and validate user preferences."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


SETTINGS_PATH = Path.home() / ".codex" / "settings.json"

SETTINGS_META = {
    "theme": {
        "label": "Color Theme",
        "type": "choice",
        "choices": ["dark", "dracula", "nord", "monokai", "gruvbox", "solarized_dark", "solarized_light", "high_contrast", "claude"],
        "group": "Appearance",
    },
    "syntax_theme": {
        "label": "Code Syntax Theme",
        "type": "choice",
        "choices": ["monokai", "dracula", "github-dark", "solarized-dark", "solarized-light", "vs", "friendly"],
        "group": "Appearance",
    },
    "layout": {
        "label": "Layout Mode",
        "type": "choice",
        "choices": ["auto", "compact", "standard", "wide"],
        "group": "Layout",
        "hint": "auto detects terminal width",
    },
    "dynamic_margins": {
        "label": "Dynamic Margins",
        "type": "bool",
        "group": "Layout",
        "hint": "scale margins to terminal width",
    },
    "word_wrap": {
        "label": "Word Wrap",
        "type": "bool",
        "group": "Layout",
    },
    "font_decorations": {
        "label": "Bold / Italic Text",
        "type": "bool",
        "group": "Appearance",
    },
    "ascii_art_headers": {
        "label": "ASCII Art Headers",
        "type": "bool",
        "group": "Appearance",
        "hint": "large word art for topic banners",
    },
    "show_word_art": {
        "label": "Word Art in Lessons",
        "type": "bool",
        "group": "Appearance",
    },
    "emoji": {
        "label": "Emoji Icons",
        "type": "bool",
        "group": "Appearance",
        "hint": "use emoji instead of ASCII prefixes",
    },
    "show_breadcrumbs": {
        "label": "Show Breadcrumbs",
        "type": "bool",
        "group": "Navigation",
    },
    "line_numbers": {
        "label": "Code Line Numbers",
        "type": "bool",
        "group": "Content",
    },
    "show_facts": {
        "label": "Show Facts & Notes",
        "type": "bool",
        "group": "Content",
    },
    "show_tips": {
        "label": "Show Tips",
        "type": "bool",
        "group": "Content",
    },
    "show_progress_bar": {
        "label": "Progress Bar",
        "type": "bool",
        "group": "Display",
    },
    "highlight_on_completion": {
        "label": "Highlight Completed",
        "type": "bool",
        "group": "Display",
    },
    "compact_menus": {
        "label": "Compact Menus",
        "type": "bool",
        "group": "Layout",
        "hint": "tighter spacing for small screens",
    },
    "pager_scroll_lines": {
        "label": "Scroll Step (lines)",
        "type": "int",
        "min": 1,
        "max": 20,
        "group": "Navigation",
    },
    "animation": {
        "label": "Animations",
        "type": "bool",
        "group": "Display",
        "hint": "loading spinners and transitions",
    },
}


@dataclass
class Config:
    theme: str = "dark"
    syntax_theme: str = "monokai"
    layout: str = "auto"
    dynamic_margins: bool = True
    word_wrap: bool = True
    font_decorations: bool = True
    ascii_art_headers: bool = True
    show_word_art: bool = True
    emoji: bool = False
    show_breadcrumbs: bool = True
    line_numbers: bool = True
    show_facts: bool = True
    show_tips: bool = True
    show_progress_bar: bool = True
    highlight_on_completion: bool = True
    compact_menus: bool = False
    pager_scroll_lines: int = 5
    animation: bool = True

    @classmethod
    def load(cls, path: Path = SETTINGS_PATH) -> "Config":
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
                return cls(**valid)
            except Exception:
                pass
        return cls()

    def save(self, path: Path = SETTINGS_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def get(self, key: str) -> Any:
        return getattr(self, key)

    def set(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
