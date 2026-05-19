"""Inverted index with fuzzy matching for full-text search across CODEX content."""

import re
from difflib import SequenceMatcher, get_close_matches
from typing import Any


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "is", "it", "its", "be", "by", "as", "are", "was",
    "with", "this", "that", "from", "which", "can", "will", "not",
    "has", "have", "had", "do", "does", "did", "more", "than",
}


class SearchIndex:
    def __init__(self):
        self._index: dict[str, list[dict]] = {}
        self._documents: list[dict] = []

    def build(self, lessons: list[dict]) -> None:
        self._index.clear()
        self._documents.clear()

        for lesson in lessons:
            doc_id = len(self._documents)
            text = self._extract_text(lesson)
            self._documents.append({
                "id":           doc_id,
                "lesson_id":    lesson.get("id", ""),
                "lesson_title": lesson.get("title", ""),
                "topic_id":     lesson.get("topic_id", ""),
                "topic_name":   lesson.get("topic_name", ""),
                "text":         text[:500],
            })
            for token in self._tokenize(text):
                self._index.setdefault(token, [])
                if doc_id not in [d["id"] for d in self._index[token]]:
                    self._index[token].append(self._documents[doc_id])

    def search(self, query: str, limit: int = 10) -> list[dict]:
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores: dict[int, float] = {}

        # Phase 1: exact token match (weight 2) and prefix match (weight 1)
        for token in tokens:
            for doc in self._index.get(token, []):
                scores[doc["id"]] = scores.get(doc["id"], 0) + 2.0
            for key, docs in self._index.items():
                if key != token and token in key:
                    for doc in docs:
                        scores[doc["id"]] = scores.get(doc["id"], 0) + 1.0

        # Phase 2: fuzzy match when results are sparse (fills typo/near-miss gaps)
        if len(scores) < 5:
            for token in tokens:
                for key, docs in self._index.items():
                    if key == token or token in key:
                        continue  # already counted above
                    ratio = SequenceMatcher(None, token, key).ratio()
                    if ratio >= 0.68:
                        for doc in docs:
                            scores[doc["id"]] = scores.get(doc["id"], 0) + ratio * 0.8

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in ranked[:limit]:
            doc = self._documents[doc_id].copy()
            doc["excerpt"] = self._excerpt(doc.get("text", ""), query)
            doc["score"] = score
            results.append(doc)

        return results

    def suggest(self, query: str) -> list[str]:
        """Return up to 3 close index terms for 'Did you mean?' suggestions."""
        tokens = self._tokenize(query)
        if not tokens:
            return []
        all_keys = list(self._index.keys())
        suggestions: set[str] = set()
        for token in tokens:
            for match in get_close_matches(token, all_keys, n=3, cutoff=0.65):
                suggestions.add(match)
        return sorted(suggestions)[:3]

    def _extract_text(self, lesson: dict) -> str:
        parts = [
            lesson.get("title", ""),
            lesson.get("subtitle", ""),
            " ".join(lesson.get("tags", [])),
        ]
        for section in lesson.get("sections", []):
            for field in ("content", "formula", "prompt", "answer", "art"):
                if section.get(field):
                    parts.append(str(section[field]))
            for item in section.get("items", []):
                parts.append(str(item))
            for k, v in section.get("variables", {}).items():
                parts.append(f"{k} {v}")
        return " ".join(parts)

    def _tokenize(self, text: str) -> list[str]:
        words = re.findall(r"[a-z0-9]+", text.lower())
        return [w for w in words if w not in STOP_WORDS and len(w) > 1]

    def _excerpt(self, text: str, query: str, length: int = 100) -> str:
        lower = text.lower()
        query_lower = query.lower()
        pos = lower.find(query_lower)
        if pos == -1:
            return text[:length]
        start = max(0, pos - 30)
        end = min(len(text), start + length)
        excerpt = text[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        return excerpt
