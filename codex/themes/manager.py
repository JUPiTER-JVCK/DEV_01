"""Theme manager — resolves styles from the active theme."""

from .definitions import THEMES, DEFAULT_THEME


class ThemeManager:
    def __init__(self, theme_name: str = DEFAULT_THEME):
        self._name = theme_name if theme_name in THEMES else DEFAULT_THEME
        self._theme = THEMES[self._name]

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_dark(self) -> bool:
        return self._theme.get("dark", True)

    def set_theme(self, name: str) -> None:
        if name in THEMES:
            self._name = name
            self._theme = THEMES[name]

    def s(self, key: str) -> str:
        """Return the Rich style string for a theme key."""
        return self._theme.get(key, "")

    def syntax_theme(self) -> str:
        return self._theme.get("syntax", "monokai")

    @staticmethod
    def available() -> list[str]:
        return list(THEMES.keys())

    @staticmethod
    def info(name: str) -> dict:
        return THEMES.get(name, {})
