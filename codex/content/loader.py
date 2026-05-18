"""Content loader — reads YAML topic and lesson files."""

from pathlib import Path
from typing import Any
import yaml

CONTENT_DIR = Path(__file__).parent / "topics"


class ContentLoader:
    def __init__(self, content_dir: Path = CONTENT_DIR):
        self._dir = content_dir
        self._cache: dict[str, Any] = {}

    def list_topics(self) -> list[dict]:
        meta_path = self._dir / "_meta.yaml"
        if not meta_path.exists():
            return []
        data = self._load_yaml(meta_path)
        return data.get("topics", [])

    def list_lessons(self, topic_id: str) -> list[dict]:
        topic_dir = self._dir / topic_id
        meta_path = topic_dir / "_topic.yaml"
        if not meta_path.exists():
            return []
        data = self._load_yaml(meta_path)
        return data.get("lessons", [])

    def lesson_count(self, topic_id: str) -> int:
        return len(self.list_lessons(topic_id))

    def load_lesson(self, topic_id: str, lesson_id: str) -> dict | None:
        cache_key = f"{topic_id}/{lesson_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        topic_dir = self._dir / topic_id
        lessons = self.list_lessons(topic_id)
        for lesson_meta in lessons:
            if lesson_meta["id"] == lesson_id:
                filename = lesson_meta.get("file", f"{lesson_id}.yaml")
                path = topic_dir / filename
                if path.exists():
                    data = self._load_yaml(path)
                    data.setdefault("id", lesson_id)
                    self._cache[cache_key] = data
                    return data
        return None

    def all_lessons(self) -> list[dict]:
        result = []
        for topic in self.list_topics():
            for lesson in self.list_lessons(topic["id"]):
                lesson["topic_id"] = topic["id"]
                lesson["topic_name"] = topic["name"]
                result.append(lesson)
        return result

    def all_lesson_content(self) -> list[dict]:
        result = []
        for topic in self.list_topics():
            for lesson_meta in self.list_lessons(topic["id"]):
                lesson = self.load_lesson(topic["id"], lesson_meta["id"])
                if lesson:
                    lesson["topic_id"] = topic["id"]
                    lesson["topic_name"] = topic["name"]
                    result.append(lesson)
        return result

    def _load_yaml(self, path: Path) -> dict:
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
            data = yaml.safe_load(raw) or {}
            return self._post_process(data)
        except Exception as e:
            # Re-try with art block normalization
            try:
                with open(path, encoding="utf-8") as f:
                    raw = f.read()
                normalized = self._normalize_art_blocks(raw)
                data = yaml.safe_load(normalized) or {}
                return self._post_process(data)
            except Exception as e2:
                return {"_error": str(e2)}

    @staticmethod
    def _normalize_art_blocks(raw: str) -> str:
        """Fix varying indentation in art: | blocks for PyYAML compatibility."""
        import re
        lines = raw.splitlines()
        result = []
        in_art = False
        base_indent = 0

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip()

            # Detect 'art: |' key
            m = re.match(r'^(\s*)art:\s*\|[-+]?\s*$', stripped)
            if m:
                base_indent = len(m.group(1))
                result.append(stripped)
                i += 1
                in_art = True
                art_lines = []

                # Collect all art lines (indented > base_indent)
                while i < len(lines):
                    al = lines[i]
                    # Empty lines belong to the block
                    if al.strip() == "":
                        art_lines.append("")
                        i += 1
                        continue
                    # Lines more indented than base belong to the art block
                    if len(al) > 0 and len(al) - len(al.lstrip()) > base_indent:
                        art_lines.append(al)
                        i += 1
                    else:
                        break

                # Find minimum non-empty indentation
                indents = [len(al) - len(al.lstrip())
                           for al in art_lines if al.strip()]
                min_indent = min(indents) if indents else base_indent + 2

                # Re-emit art lines, normalizing to min_indent first line
                # Add a sentinel first line to force PyYAML indentation detection
                sentinel = " " * min_indent
                result.append(sentinel)
                for al in art_lines:
                    result.append(al)
                continue

            result.append(line)
            i += 1

        return "\n".join(result)

    @staticmethod
    def _post_process(data: dict) -> dict:
        """Strip leading blank lines from art fields."""
        for section in data.get("sections", []):
            if "art" in section and isinstance(section["art"], str):
                art = section["art"]
                # Strip sentinel empty first line added by normalization
                lines = art.splitlines()
                while lines and not lines[0].strip():
                    lines.pop(0)
                section["art"] = "\n".join(lines)
        return data
