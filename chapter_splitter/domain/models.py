from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SplitRule:
    name: str
    pattern: str
    level: str
    split: bool
    priority: int


class SplitException(Exception):
    """Base exception for split chapter operations."""


@dataclass
class ChapterSegment:
    title: str
    level: str
    body: str = ""
    source_line: int = 0
    ignored: bool = False

    @property
    def body_lines(self) -> list[str]:
        return self.body.splitlines()


@dataclass
class PreviewEntry:
    index: int
    title: str
    level: str
    split: bool
    body_characters: int
    sequence_warning: str | None
    source_line: int
    ignored: bool = False


@dataclass
class SplitResult:
    segments: list[ChapterSegment] = field(default_factory=list)
    preview: list[PreviewEntry] = field(default_factory=list)
    exported_files: list[str] = field(default_factory=list)
