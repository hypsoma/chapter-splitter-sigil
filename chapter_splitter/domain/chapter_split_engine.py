from __future__ import annotations

import io
import re

from .models import ChapterSegment, SplitRule

PREFACE_TITLE = "序言"


class RegexPatternEvaluator:
    def __init__(self, rules: list[SplitRule]) -> None:
        # Sort rules by priority once during initialization.
        sorted_rules = sorted(rules, key=lambda r: r.priority)
        self._compiled = tuple((rule, re.compile(rule.pattern)) for rule in sorted_rules)

    def match(self, line: str) -> SplitRule | None:
        for rule, pattern in self._compiled:
            if pattern.match(line):
                return rule
        return None


class ChapterSplitEngine:
    def __init__(self, rules: list[SplitRule]) -> None:
        self._evaluator = RegexPatternEvaluator(rules)
        self._compiled_rules = self._evaluator._compiled

    def split(self, sanitized_text: str) -> list[ChapterSegment]:
        if not sanitized_text:
            return []

        segments: list[ChapterSegment] = []
        current_title = PREFACE_TITLE
        current_level = "h2"
        current_source_line = 1
        segment_has_visible_content = False

        # Use StringIO to accumulate lines efficiently
        buffer = io.StringIO()
        _write = buffer.write
        _compiled_rules = self._compiled_rules

        if not _compiled_rules:
            if sanitized_text.isspace():
                return []
            return [
                ChapterSegment(
                    title=PREFACE_TITLE,
                    level=current_level,
                    body=sanitized_text,
                    source_line=current_source_line,
                )
            ]

        def flush_segment() -> None:
            nonlocal segment_has_visible_content
            content = buffer.getvalue()
            # Keep previous semantics: skip only an empty initial preface.
            if segment_has_visible_content or current_title != PREFACE_TITLE:
                segments.append(
                    ChapterSegment(
                        title=current_title,
                        level=current_level,
                        body=content,
                        source_line=current_source_line,
                    )
                )
            buffer.truncate(0)
            buffer.seek(0)
            segment_has_visible_content = False

        for line_no, raw_line in enumerate(io.StringIO(sanitized_text), start=1):
            stripped_line = raw_line.strip()
            matched = None
            for rule, pattern in _compiled_rules:
                if pattern.match(stripped_line):
                    matched = rule
                    break

            if matched and matched.split:
                flush_segment()
                current_title = stripped_line
                current_level = matched.level
                current_source_line = line_no
                heading = f"<{matched.level}>{stripped_line}</{matched.level}>\n"
                _write(heading)
                segment_has_visible_content = True
                continue

            if matched and not matched.split:
                heading = f"<{matched.level}>{stripped_line}</{matched.level}>\n"
                _write(heading)
                segment_has_visible_content = True
                continue

            _write(raw_line)
            if not segment_has_visible_content and raw_line and not raw_line.isspace():
                segment_has_visible_content = True

        flush_segment()
        return segments
