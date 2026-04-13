from __future__ import annotations

import io
import re

# Pre-compile constants to avoid overhead in loops.
_HEADING_PATTERN = re.compile(r"^<h[1-6][^>]*>.*</h[1-6]>$", re.IGNORECASE)


class ParagraphRenderer:
    @staticmethod
    def render(main_text: str | list[str], indent: str = "  ") -> str:
        # Avoid creating intermediate strings when processing many paragraphs.
        buffer = io.StringIO()
        _write = buffer.write

        # Split on \n directly, as most modern text is normalized or small enough here.
        lines = main_text if isinstance(main_text, list) else main_text.splitlines()
        last_idx = len(lines) - 1

        for i, line in enumerate(lines):
            content = line.strip()
            if not content:
                continue

            _write(indent)
            if _HEADING_PATTERN.match(content):
                _write(content)
            else:
                _write("<p>")
                _write(content)
                _write("</p>")

            if i < last_idx:
                _write("\n")

        return buffer.getvalue()
