from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import tomllib

from chapter_splitter.domain.preset_catalog import (
    NAME_KEY_LABEL,
    build_preset_key_by_pattern_level,
)
from chapter_splitter.domain.template_injector import DEFAULT_TEMPLATE

DEFAULT_CONFIG_PATH = Path(__file__).with_name("default_config.toml")


def _normalize_preset_config(data: dict[str, Any]) -> None:
    enabled = data.get("enabled_builtin_preset_keys")
    if isinstance(enabled, list):
        data["enabled_builtin_preset_keys"] = [
            str(key).strip() for key in enabled if str(key).strip()
        ]
    else:
        data["enabled_builtin_preset_keys"] = []

    custom = data.get("custom_presets")
    normalized_custom: list[dict[str, str]] = []
    if isinstance(custom, list):
        for preset in custom:
            if not isinstance(preset, dict):
                continue
            pattern = str(preset.get("pattern", "")).strip()
            if not pattern:
                continue
            normalized_custom.append(
                {
                    "name": str(preset.get("name", "")).strip(),
                    "pattern": pattern,
                    "level": str(preset.get("level", "h2")).strip() or "h2",
                }
            )
    data["custom_presets"] = normalized_custom


def _load_default_config() -> dict[str, Any]:
    data = tomllib.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    _normalize_preset_config(data)
    templates = data.get("templates")
    if not isinstance(templates, dict):
        templates = {}
    default_template = str(templates.get("default", "")).strip()
    templates["default"] = default_template or DEFAULT_TEMPLATE
    data["templates"] = templates
    return data


DEFAULT_CONFIG = _load_default_config()
DEFAULT_RULES = copy.deepcopy(DEFAULT_CONFIG.get("rules", []))
DEFAULT_ENABLED_BUILTIN_PRESET_KEYS = copy.deepcopy(
    DEFAULT_CONFIG.get("enabled_builtin_preset_keys", [])
)
DEFAULT_CUSTOM_PRESETS = copy.deepcopy(DEFAULT_CONFIG.get("custom_presets", []))
DEFAULT_NAME_RULES = dict(DEFAULT_CONFIG.get("name_rules", {}))
DEFAULT_OUTPUT_DIR = str(DEFAULT_CONFIG.get("output_dir", "output"))
DEFAULT_MAX_REGEX = int(DEFAULT_CONFIG.get("ui", {}).get("max_regex", 15))
DEFAULT_AUTO_ANALYZE_MAX_RULES_PER_LEVEL = max(
    1, int(DEFAULT_CONFIG.get("ui", {}).get("auto_analyze_max_rules_per_level", 2))
)
DEFAULT_LONG_TITLE_THRESHOLD = int(
    DEFAULT_CONFIG.get("ui", {}).get("long_title_threshold", 30)
)
DEFAULT_REMOVE_EMPTY_LINES = bool(
    DEFAULT_CONFIG.get("ui", {}).get("remove_empty_lines", False)
)
DEFAULT_STRIP_PARAGRAPH_INDENT = bool(
    DEFAULT_CONFIG.get("ui", {}).get("strip_paragraph_indent", False)
)
DEFAULT_UI_LANGUAGE = str(DEFAULT_CONFIG.get("ui", {}).get("language", "auto"))
SUPPORTED_UI_LANGUAGES = frozenset(
    str(item) for item in DEFAULT_CONFIG.get("supported_ui_languages", ["zh", "en"])
)
DEFAULT_UI = {
    "max_regex": DEFAULT_MAX_REGEX,
    "auto_analyze_max_rules_per_level": DEFAULT_AUTO_ANALYZE_MAX_RULES_PER_LEVEL,
    "long_title_threshold": DEFAULT_LONG_TITLE_THRESHOLD,
    "remove_empty_lines": DEFAULT_REMOVE_EMPTY_LINES,
    "strip_paragraph_indent": DEFAULT_STRIP_PARAGRAPH_INDENT,
    "language": DEFAULT_UI_LANGUAGE,
}
PRESET_KEY_BY_PATTERN_LEVEL = build_preset_key_by_pattern_level()
LOCALIZED_DEFAULT_NAMES = {
    key: set(labels.values()) for key, labels in NAME_KEY_LABEL.items()
}


class ConfigurationManager:
    @staticmethod
    def default_config() -> dict[str, Any]:
        return {
            "rules": copy.deepcopy(DEFAULT_RULES),
            "enabled_builtin_preset_keys": copy.deepcopy(
                DEFAULT_ENABLED_BUILTIN_PRESET_KEYS
            ),
            "custom_presets": copy.deepcopy(DEFAULT_CUSTOM_PRESETS),
            "templates": {"default": str(DEFAULT_CONFIG["templates"]["default"])},
            "name_rules": dict(DEFAULT_NAME_RULES),
            "ui": dict(DEFAULT_UI),
        }

    @staticmethod
    def load(path: Path) -> dict[str, Any]:
        if not path.exists():
            return ConfigurationManager.default_config()
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        _normalize_preset_config(data)
        data["rules"] = ConfigurationManager._normalize_rules(data.get("rules", []))
        return data

    @staticmethod
    def _normalize_rules(raw_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_rules: list[dict[str, Any]] = []
        for rule in raw_rules:
            copied = dict(rule)
            pattern = str(copied.get("pattern", ""))
            level = str(copied.get("level", ""))
            name_key = str(copied.get("name_key", "")).strip()
            custom_name = str(copied.get("custom_name", "")).strip()

            if not name_key:
                name_key = PRESET_KEY_BY_PATTERN_LEVEL.get((pattern, level), "")
            if name_key:
                copied["name_key"] = name_key

            candidate_name = custom_name
            default_names = LOCALIZED_DEFAULT_NAMES.get(name_key, set())
            if candidate_name and candidate_name not in default_names:
                copied["custom_name"] = candidate_name
            else:
                copied.pop("custom_name", None)
            copied.pop("name", None)
            normalized_rules.append(copied)
        return normalized_rules

    @staticmethod
    def save(path: Path, data: dict[str, Any]) -> None:
        output: list[str] = []
        output.append(
            "enabled_builtin_preset_keys = "
            + json.dumps(data.get("enabled_builtin_preset_keys", []), ensure_ascii=False)
        )
        output.append("")

        for rule in data.get("rules", []):
            output.append("[[rules]]")
            for key, value in rule.items():
                output.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
            output.append("")

        for preset in data.get("custom_presets", []):
            output.append("[[custom_presets]]")
            for key, value in preset.items():
                output.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
            output.append("")

        for table in ("templates", "name_rules", "ui"):
            output.append(f"[{table}]")
            for key, value in data.get(table, {}).items():
                output.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
            output.append("")

        path.write_text("\n".join(output).strip() + "\n", encoding="utf-8")
