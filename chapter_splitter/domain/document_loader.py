from __future__ import annotations

import html
import re
from pathlib import Path


SUPPORTED_ENCODINGS = ("utf-8", "utf-16", "gbk")


class DocumentLoader:
    @staticmethod
    def load_text(path: Path) -> str:
        payload = path.read_bytes()
        for encoding in SUPPORTED_ENCODINGS:
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("auto", b"", 0, 1, f"Unsupported encoding: {path}")

    _ENTITY_PATTERN = re.compile(r"&amp;([a-zA-Z][a-zA-Z0-9]+;)")

    @staticmethod
    def sanitize_text(raw_text: str) -> str:
        escaped = html.escape(raw_text, quote=False)
        return DocumentLoader._ENTITY_PATTERN.sub(r"&\1", escaped)

    @staticmethod
    def preprocess_text(
        raw_text: str, remove_empty_lines: bool = False, strip_indent: bool = False
    ) -> str:
        if not remove_empty_lines and not strip_indent:
            return raw_text

        lines = raw_text.splitlines()

        if strip_indent and remove_empty_lines:
            return "\n".join(
                normalized for line in lines if (normalized := line.lstrip(" \t\u3000"))
            )
        if strip_indent:
            return "\n".join(line.lstrip(" \t\u3000") for line in lines)
        if remove_empty_lines:
            return "\n".join(line for line in lines if line.strip())

        return raw_text
