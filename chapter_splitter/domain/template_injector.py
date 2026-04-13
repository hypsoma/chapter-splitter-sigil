from __future__ import annotations

import re


from .models import ChapterSegment
from .paragraph_renderer import ParagraphRenderer


DEFAULT_TEMPLATE = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<!DOCTYPE html>
<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\">
<head>
  <title>[TITLE]</title>
  <link href=\"../Styles/Style0001.css\" type=\"text/css\" rel=\"stylesheet\"/>
</head>
<body>
  [MAIN]
</body>
</html>
"""

TITLE_PLACEHOLDER = "[TITLE]"
MAIN_PLACEHOLDER = "[MAIN]"
INTERNAL_MAIN_MARKER = "###MAIN###"


class TemplateInjector:
    def __init__(self, templates: dict[str, str]) -> None:
        raw_templates = templates or {"default": DEFAULT_TEMPLATE}
        self._parsed_cache: dict[str, tuple[str, str, str, str]] = {}

        for key, raw in raw_templates.items():
            self._parsed_cache[key] = self._parse_template(raw)

    def render_chapter(self, segment: ChapterSegment) -> str:
        # Use level-specific template or fall back to 'default'.
        parsed = (
            self._parsed_cache.get(segment.level)
            or self._parsed_cache.get("default")
            or self._parse_template(DEFAULT_TEMPLATE)
        )

        prefix, mid_prefix, suffix, indent = parsed

        # Paragraph rendering is the bottleneck, now optimized via ParagraphRenderer.
        body_content = ParagraphRenderer.render(segment.body, indent=indent)

        # Efficient assembly without multiple regex/replace calls.
        return f"{prefix}{segment.title}{mid_prefix}{body_content}{suffix}"

    @staticmethod
    def _parse_template(template: str) -> tuple[str, str, str, str]:
        """Split template into Prefix, Title-Content gap, and Post-Main content."""
        # Prefer line-start [MAIN] so we preserve the newline before content.
        main_match = re.search(rf"(?m)^([ \t]*){re.escape(MAIN_PLACEHOLDER)}", template)
        if main_match:
            main_pos = main_match.start()
            main_full_str = main_match.group(0)
            indent = main_match.group(1) or ""
        else:
            main_pos = template.find(MAIN_PLACEHOLDER)
            main_full_str = MAIN_PLACEHOLDER
            indent = ""

        if main_pos == -1:
            # Fallback if [MAIN] is missing from template
            main_pos = len(template)
            main_full_str = ""

        # Replace [MAIN] with empty but keep track of position
        temp_wo_main = (
            template[:main_pos]
            + INTERNAL_MAIN_MARKER
            + template[main_pos + len(main_full_str) :]
        )

        # Find where [TITLE] is
        title_pos = temp_wo_main.find(TITLE_PLACEHOLDER)
        if title_pos == -1:
            # No title, just return placeholder logic
            mid_marker = temp_wo_main.find(INTERNAL_MAIN_MARKER)
            prefix = temp_wo_main[:mid_marker]
            suffix = temp_wo_main[mid_marker + len(INTERNAL_MAIN_MARKER) :]
            return prefix, "", suffix, indent

        prefix = temp_wo_main[:title_pos]
        after_title = temp_wo_main[title_pos + len(TITLE_PLACEHOLDER) :]

        main_marker_pos = after_title.find(INTERNAL_MAIN_MARKER)
        mid = after_title[:main_marker_pos]
        suffix = after_title[main_marker_pos + len(INTERNAL_MAIN_MARKER) :]

        return prefix, mid, suffix, indent
