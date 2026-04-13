from __future__ import annotations

import re
from dataclasses import dataclass

from chapter_splitter.domain.preset_catalog import BUILTIN_PRESET_BY_KEY


@dataclass(frozen=True)
class PresetRule:
    pattern: str
    level: str
    name: str


def _builtin_preset(name_key: str, language: str, display_name: str) -> PresetRule:
    selected = BUILTIN_PRESET_BY_KEY[name_key][language]
    return PresetRule(selected["pattern"], selected["level"], display_name)


PRESET_RULES = [
    _builtin_preset("volume_title", "zh", "卷标题"),
    _builtin_preset("volume_alt_title", "zh", "卷标题备选"),
    _builtin_preset("preface_afterword_title", "zh", "序后简介标题"),
    _builtin_preset("chapter_title", "zh", "章标题"),
    _builtin_preset("chapter_en_title", "zh", "英文章标题"),
    _builtin_preset("section_title", "zh", "节标题"),
    _builtin_preset("episode_title", "zh", "回目标题"),
    _builtin_preset("chapter_en_title", "en", "English Chapter"),
    _builtin_preset("volume_title", "en", "English Volume"),
    _builtin_preset("volume_alt_title", "en", "English Prologue/Epilogue"),
]


class RuleAnalyzer:
    def __init__(self, candidate_rules: list[PresetRule] | None = None) -> None:
        self._candidate_rules = tuple(candidate_rules or PRESET_RULES)

    @classmethod
    def from_preset_items(cls, preset_items: list[dict[str, str]]) -> RuleAnalyzer:
        candidate_rules: list[PresetRule] = []
        seen_pattern_level: set[tuple[str, str]] = set()
        for item in preset_items:
            pattern = str(item.get("pattern", "")).strip()
            level = str(item.get("level", "h2")).strip() or "h2"
            if not pattern:
                continue
            identity = (pattern, level)
            if identity in seen_pattern_level:
                continue
            seen_pattern_level.add(identity)
            candidate_rules.append(
                PresetRule(pattern=pattern, level=level, name=str(item.get("name", "")).strip())
            )
        return cls(candidate_rules)

    def suggest(self, lines: list[str], max_rules_per_level: int = 1) -> list[PresetRule]:
        head_sample = lines[:6000]
        content = "\n".join(head_sample)
        scored: list[tuple[int, PresetRule]] = []
        for preset in self._candidate_rules:
            compiled = re.compile(preset.pattern, re.MULTILINE)
            hit_count = len(compiled.findall(content))
            if hit_count > 0:
                scored.append((hit_count, preset))

        scored.sort(key=lambda item: (-item[0], item[1].level, item[1].name))

        level_limit = max(1, int(max_rules_per_level))
        selected: list[PresetRule] = []
        selected_count_by_level: dict[str, int] = {}
        for _, rule in scored:
            current_count = selected_count_by_level.get(rule.level, 0)
            if current_count >= level_limit:
                continue
            selected.append(rule)
            selected_count_by_level[rule.level] = current_count + 1

        if not selected:
            selected = self._fallback_rules(content)
        return selected

    @staticmethod
    def _fallback_rules(content: str) -> list[PresetRule]:
        # Keep fallback strict enough to avoid low-quality broad patterns.
        fallback: list[PresetRule] = []
        if re.search(r"^第.+章", content, re.MULTILINE):
            fallback.append(PresetRule(r"^第[零一二三四五六七八九十百千万两〇0-9０-９]+章.*$", "h2", "章标题兜底"))
        if re.search(r"^第.+节", content, re.MULTILINE):
            fallback.append(PresetRule(r"^第[零一二三四五六七八九十百千万两〇0-9０-９]+节.*$", "h3", "节标题兜底"))
        return fallback
