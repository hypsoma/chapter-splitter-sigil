from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from chapter_splitter.domain.chapter_split_engine import ChapterSplitEngine
from chapter_splitter.domain.document_loader import DocumentLoader
from chapter_splitter.domain.models import SplitResult, SplitRule, SplitException
from chapter_splitter.domain.name_generator import NameGenerator
from chapter_splitter.domain.sequence_validator import SequenceValidator
from chapter_splitter.domain.template_injector import TemplateInjector


class SplitChapterService:
    def execute(
        self,
        input_path: Path,
        output_dir: Path,
        config: dict[str, Any],
        ignored_indices: set[int] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        write_output: bool = True,
        output_writer: Callable[[str, str], None] | None = None,
    ) -> SplitResult:
        ignored_indices = ignored_indices or set()

        try:
            raw_text = DocumentLoader.load_text(input_path)
            ui = config.get("ui", {})
            raw_text = DocumentLoader.preprocess_text(
                raw_text,
                remove_empty_lines=bool(ui.get("remove_empty_lines", False)),
                strip_indent=bool(ui.get("strip_paragraph_indent", False)),
            )
            sanitized = DocumentLoader.sanitize_text(raw_text)

            rules = [
                SplitRule(
                    name=str(
                        item.get("name_key")
                        or item.get("custom_name")
                        or f"rule_{index + 1}"
                    ),
                    pattern=str(item["pattern"]),
                    level=str(item.get("level", "h2")),
                    split=bool(item.get("split", True)),
                    priority=int(item.get("priority", 100)),
                )
                for index, item in enumerate(config.get("rules", []))
            ]
            segments = ChapterSplitEngine(rules).split(sanitized)
        except Exception as e:
            raise SplitException(f"Failed to process text: {e}") from e

        for index in ignored_indices:
            if 0 <= index < len(segments):
                segments[index].ignored = True

        validator = SequenceValidator()
        preview = validator.build_preview(segments)

        if write_output:
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise SplitException(f"Failed to create output directory: {e}") from e

        name_generator = NameGenerator(config.get("name_rules", {}))
        injector = TemplateInjector(config.get("templates", {}))

        exported_files: list[str] = []
        total = sum(1 for segment in segments if not segment.ignored)
        written = 0
        should_render_output = write_output or output_writer is not None

        for segment in segments:
            if segment.ignored:
                continue

            try:
                file_name = name_generator.next(segment)
                if should_render_output:
                    xhtml = injector.render_chapter(segment)
                if write_output:
                    (output_dir / file_name).write_text(xhtml, encoding="utf-8")
                if output_writer is not None:
                    output_writer(file_name, xhtml)
                if should_render_output:
                    exported_files.append(file_name)
                written += 1
                if progress_callback is not None:
                    progress_callback(written, total)
            except Exception as e:
                raise SplitException(f"Failed writing chapter '{segment.title}': {e}") from e

        return SplitResult(segments=segments, preview=preview, exported_files=exported_files)
