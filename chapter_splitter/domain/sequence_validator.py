from __future__ import annotations

import re

from .models import ChapterSegment, PreviewEntry


CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
CHINESE_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}
FULL_WIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


_ARABIC_PATTERN = re.compile(r"\d+")
_CHINESE_PATTERN = re.compile(r"[零〇一二两三四五六七八九十百千万]+")
_WHITESPACE_RUN_PATTERN = re.compile(r"\s+")


def _level_number(level: str) -> int:
    try:
        return int(level[1:])
    except (ValueError, IndexError):
        return 6


class SequenceValidator:
    def build_preview(self, segments: list[ChapterSegment]) -> list[PreviewEntry]:
        numbers = [self.extract_number(s.title) for s in segments]

        # Scope-aware grouping: higher-level headings reset lower-level
        # tracking. Build scope boundaries so that chapter numbering restarts
        # when a new parent heading appears (e.g. h1 resets h2).
        scope_ids = self._assign_scope_ids(segments)

        # Two-pass bidirectional check
        warnings = self._check_sequences(segments, numbers, scope_ids)

        entries: list[PreviewEntry] = []
        for idx, segment in enumerate(segments):
            body_chars = self._visible_char_count(segment.body)
            entries.append(
                PreviewEntry(
                    index=idx,
                    title=segment.title,
                    level=segment.level,
                    split=not segment.ignored,
                    body_characters=body_chars,
                    sequence_warning=warnings.get(idx),
                    source_line=segment.source_line,
                    ignored=segment.ignored,
                )
            )
        return entries

    def _assign_scope_ids(self, segments: list[ChapterSegment]) -> list[str]:
        """Assign a scope identifier to each segment.

        A segment's scope is determined by its ancestor headings.  h2
        chapters under the same h1 share a scope; a new h1 resets the
        scope for all h2/h3/... beneath it.
        """
        # Tracks the latest counter for each level that acts as a parent
        # scope boundary.  When h1 #2 appears, all h2 chapters after it
        # belong to scope "h1:2" until h1 #3 appears.
        parent_counters: dict[int, int] = {}
        scope_ids: list[str] = []

        for segment in segments:
            level = _level_number(segment.level)

            # Increment this level's counter (marks a new parent scope for
            # deeper levels) and clear deeper counters.
            parent_counters[level] = parent_counters.get(level, 0) + 1
            for deeper in range(level + 1, 7):
                parent_counters.pop(deeper, None)

            # The scope for this segment is built from ancestors ABOVE it.
            # Segments at the same level under the same parent share a scope.
            scope_parts = []
            for ancestor in range(1, level):
                scope_parts.append(f"{ancestor}:{parent_counters.get(ancestor, 0)}")
            scope_id = f"{segment.level}|{'_'.join(scope_parts)}"
            scope_ids.append(scope_id)

        return scope_ids

    def _check_sequences(
        self,
        segments: list[ChapterSegment],
        numbers: list[int | None],
        scope_ids: list[str],
    ) -> dict[int, str]:
        """Bidirectional sequence check within each scope group."""
        # Group indices by scope
        scope_groups: dict[str, list[int]] = {}
        for idx, scope_id in enumerate(scope_ids):
            if numbers[idx] is not None:
                scope_groups.setdefault(scope_id, []).append(idx)

        warnings: dict[int, str] = {}

        for _scope_id, indices in scope_groups.items():
            if len(indices) < 2:
                continue

            for pos, idx in enumerate(indices):
                number = numbers[idx]
                prev_number = numbers[indices[pos - 1]] if pos > 0 else None
                next_number = (
                    numbers[indices[pos + 1]] if pos < len(indices) - 1 else None
                )

                connects_backward = prev_number is None or number == prev_number + 1
                connects_forward = next_number is None or number + 1 == next_number

                if connects_backward and connects_forward:
                    continue

                if not connects_backward and connects_forward:
                    warnings[idx] = f"跳章（{prev_number} → {number}）"
                elif not connects_backward and not connects_forward:
                    warnings[idx] = (
                        f"编号异常（当前 {number}，前 {prev_number} / 后 {next_number}）"
                    )
                # connects_backward and not connects_forward: no warning here,
                # the NEXT entry will capture the break from its backward check.

        return warnings

    def extract_number(self, title: str) -> int | None:
        normalized = title.translate(FULL_WIDTH_DIGITS)
        arabic = _ARABIC_PATTERN.search(normalized)
        if arabic:
            return int(arabic.group())
        chinese = _CHINESE_PATTERN.search(title)
        if not chinese:
            return None
        text = chinese.group()
        if all(char in CHINESE_DIGITS for char in text):
            return int("".join(str(CHINESE_DIGITS[char]) for char in text))
        return self._parse_unit_number(text)

    def _parse_unit_number(self, text: str) -> int:
        total = 0
        section = 0
        number = 0
        for char in text:
            if char in CHINESE_DIGITS:
                number = CHINESE_DIGITS[char]
                continue
            unit = CHINESE_UNITS.get(char)
            if unit is None:
                continue
            if number == 0:
                number = 1
            section += number * unit
            number = 0
        total += section + number
        return total

    @staticmethod
    def _visible_char_count(text: str) -> int:
        whitespace_chars = 0
        for match in _WHITESPACE_RUN_PATTERN.finditer(text):
            whitespace_chars += match.end() - match.start()
        return len(text) - whitespace_chars
