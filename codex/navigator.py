"""Navigation state — screen stack, breadcrumbs, and history."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NavFrame:
    screen: str
    args: dict = field(default_factory=dict)
    label: str = ""


class Navigator:
    def __init__(self):
        self._stack: list[NavFrame] = []
        self._history: list[NavFrame] = []

    def push(self, screen: str, args: dict | None = None, label: str = "") -> None:
        frame = NavFrame(screen=screen, args=args or {}, label=label)
        self._stack.append(frame)

    def pop(self) -> NavFrame | None:
        if len(self._stack) > 1:
            frame = self._stack.pop()
            self._history.append(frame)
            return self._stack[-1]
        return self._stack[0] if self._stack else None

    def current(self) -> NavFrame | None:
        return self._stack[-1] if self._stack else None

    def replace(self, screen: str, args: dict | None = None, label: str = "") -> None:
        if self._stack:
            self._stack[-1] = NavFrame(screen=screen, args=args or {}, label=label)

    def breadcrumbs(self) -> list[str]:
        return [f.label for f in self._stack if f.label]

    def can_go_back(self) -> bool:
        return len(self._stack) > 1

    def reset(self, screen: str = "home") -> None:
        self._stack.clear()
        self._stack.append(NavFrame(screen=screen, label="CODEX"))
