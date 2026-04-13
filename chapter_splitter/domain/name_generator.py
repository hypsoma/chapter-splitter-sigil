from __future__ import annotations

import re

from .models import ChapterSegment

LEVEL_ORDER = ("h1", "h2", "h3", "h4", "h5", "h6")
LEVEL_INDEX = {level: idx for idx, level in enumerate(LEVEL_ORDER)}
DEFAULT_STEM_PATTERN = "{000}_{title}"
PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")
SLUG_SANITIZE_PATTERN = re.compile(r"[^\w\u4e00-\u9fff-]+", flags=re.UNICODE)


class NameGenerator:
    def __init__(self, rule_by_level: dict[str, str]) -> None:
        self._rule_by_level = rule_by_level
        self._absolute_counter = 0
        self._relative_by_level: dict[str, int] = {}
        self._last_title_by_level: dict[str, str] = {}
        self._last_slug_by_level: dict[str, str] = {}
        self._slug_cache: dict[str, str] = {}
        self._used: set[str] = set()

    def next(self, segment: ChapterSegment) -> str:
        self._absolute_counter += 1
        self._reset_children_when_parent_changes(segment.level)
        self._relative_by_level[segment.level] = (
            self._relative_by_level.get(segment.level, 0) + 1
        )

        title_slug = self._slugify_cached(segment.title)

        mapping = {
            "000": f"{self._absolute_counter:03d}",
            "$$$": f"{self._relative_by_level[segment.level]:03d}",
            "title": title_slug,
            "h1_no": str(self._relative_by_level.get("h1", 0)),
            "h2_no": str(self._relative_by_level.get("h2", 0)),
            "h1_no3": f"{self._relative_by_level.get('h1', 0):03d}",
            "h2_no3": f"{self._relative_by_level.get('h2', 0):03d}",
        }
        for level in LEVEL_ORDER:
            mapping[level] = self._last_slug_by_level.get(level, level)

        pattern = self._rule_by_level.get(segment.level, DEFAULT_STEM_PATTERN)
        stem = PLACEHOLDER_PATTERN.sub(
            lambda match: mapping.get(match.group(1), match.group(0)),
            pattern,
        )

        stem = self._dedupe(stem)
        self._last_title_by_level[segment.level] = segment.title
        self._last_slug_by_level[segment.level] = title_slug
        return f"{stem}.xhtml"

    def _reset_children_when_parent_changes(self, level: str) -> None:
        idx = LEVEL_INDEX[level]
        for child in LEVEL_ORDER[idx + 1 :]:
            self._relative_by_level[child] = 0

    def _dedupe(self, stem: str) -> str:
        if stem not in self._used:
            self._used.add(stem)
            return stem
        suffix = 2
        while f"{stem}_{suffix}" in self._used:
            suffix += 1
        unique = f"{stem}_{suffix}"
        self._used.add(unique)
        return unique

    def _slugify_cached(self, text: str) -> str:
        cached = self._slug_cache.get(text)
        if cached is not None:
            return cached
        slug = self._slugify(text)
        self._slug_cache[text] = slug
        return slug

    @staticmethod
    def _slugify(text: str) -> str:
        value = SLUG_SANITIZE_PATTERN.sub("_", text).strip("_")
        return value or "untitled"
