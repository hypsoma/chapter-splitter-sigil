from __future__ import annotations

from typing import TypedDict


class PresetPattern(TypedDict):
    pattern: str
    level: str


BUILTIN_PRESET_BY_KEY: dict[str, dict[str, PresetPattern]] = {
    "volume_title": {
        "zh": {
            "pattern": r"^第[零一二三四五六七八九十百千万两〇0-9０-９]+卷.*$",
            "level": "h1",
        },
        "en": {
            "pattern": r"(?i)^(?:part|book|volume)\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)\b.*$",
            "level": "h1",
        },
    },
    "chapter_title": {
        "zh": {
            "pattern": r"^第[零一二三四五六七八九十百千万两〇0-9０-９]+章.*$",
            "level": "h2",
        },
        "en": {"pattern": r"^Chapter\s+\d+.*$", "level": "h2"},
    },
    "section_title": {
        "zh": {
            "pattern": r"^第[零一二三四五六七八九十百千万两〇0-9０-９]+节.*$",
            "level": "h3",
        },
        "en": {
            "pattern": r"(?i)^section\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)\b.*$",
            "level": "h3",
        },
    },
    "episode_title": {
        "zh": {
            "pattern": r"^第[零一二三四五六七八九十百千万两〇0-9０-９]+回.*$",
            "level": "h2",
        },
        "en": {
            "pattern": r"(?i)^episode\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)\b.*$",
            "level": "h2",
        },
    },
    "volume_alt_title": {
        "zh": {
            "pattern": r"^卷[零一二三四五六七八九十百千万两〇0-9０-９]+.*$",
            "level": "h1",
        },
        "en": {
            "pattern": r"(?i)^(?:prologue|epilogue)\b.*$",
            "level": "h1",
        },
    },
    "preface_afterword_title": {
        "zh": {
            "pattern": r"^\s*(序[1-9言曲]?|(内容)?简介|后记|尾声|番外)$",
            "level": "h2",
        },
    },
    "chapter_en_title": {
        "zh": {"pattern": r"^Chapter\s+\d+.*$", "level": "h2"},
        "en": {
            "pattern": r"(?i)^chapter\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)\b.*$",
            "level": "h2",
        },
    },
}

PRESET_NAME_KEY_ORDER = [
    "volume_title",
    "chapter_title",
    "section_title",
    "episode_title",
    "volume_alt_title",
    "preface_afterword_title",
    "chapter_en_title",
]

NAME_KEY_LABEL = {
    "volume_title": {"zh": "卷标题", "en": "Volume Title"},
    "chapter_title": {"zh": "章标题", "en": "Chapter Title"},
    "section_title": {"zh": "节标题", "en": "Section Title"},
    "episode_title": {"zh": "回目标题", "en": "Episode Title"},
    "volume_alt_title": {"zh": "卷标题备选", "en": "Volume Title (Alt)"},
    "preface_afterword_title": {"zh": "序后简介标题", "en": "Preface/Afterword"},
    "chapter_en_title": {"zh": "英文章标题", "en": "Chapter Title (EN)"},
    "chapter_title_fallback": {"zh": "章标题兜底", "en": "Chapter Title Fallback"},
    "section_title_fallback": {"zh": "节标题兜底", "en": "Section Title Fallback"},
}


def build_preset_key_by_pattern_level() -> dict[tuple[str, str], str]:
    mapping: dict[tuple[str, str], str] = {}
    for name_key, options in BUILTIN_PRESET_BY_KEY.items():
        for selected in options.values():
            mapping[(selected["pattern"], selected["level"])] = name_key
    return mapping
