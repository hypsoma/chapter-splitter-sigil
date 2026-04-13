from pathlib import Path

from chapter_splitter.application.service import SplitChapterService
from chapter_splitter.infrastructure.configuration import ConfigurationManager


def test_execute_respects_ignored_indices(tmp_path: Path) -> None:
    input_path = tmp_path / "book.txt"
    input_path.write_text(
        "引子\n内容\n\n第一章 开始\nA\n\n第二章 继续\nB\n",
        encoding="utf-8",
    )

    config = ConfigurationManager.load(tmp_path / "missing.toml")
    result = SplitChapterService().execute(
        input_path=input_path,
        output_dir=tmp_path / "out",
        config=config,
        ignored_indices={2},
    )

    assert len(result.segments) >= 3
    assert len(result.exported_files) == 2
    assert not any("第二章" in name for name in result.exported_files)


def test_split_heading_is_rendered_as_h_tag(tmp_path: Path) -> None:
    input_path = tmp_path / "book_heading.txt"
    input_path.write_text("第一章 开始\n正文A\n", encoding="utf-8")
    output_dir = tmp_path / "out_heading"

    config = ConfigurationManager.default_config()
    result = SplitChapterService().execute(input_path=input_path, output_dir=output_dir, config=config, write_output=True)

    assert result.exported_files
    first_file = output_dir / result.exported_files[0]
    content = first_file.read_text(encoding="utf-8")
    assert "<h2>第一章 开始</h2>" in content
