from chapter_splitter.domain.models import ChapterSegment
from chapter_splitter.domain.document_loader import DocumentLoader
from chapter_splitter.domain.paragraph_renderer import ParagraphRenderer
from chapter_splitter.domain.rule_analyzer import RuleAnalyzer
from chapter_splitter.domain.template_injector import TemplateInjector
from chapter_splitter.infrastructure.configuration import ConfigurationManager


def test_template_injector_replaces_title_and_main() -> None:
    template = "<html><head><title>[TITLE]</title></head><body>  [MAIN]</body></html>"
    injector = TemplateInjector({"default": template})
    xhtml = injector.render_chapter(ChapterSegment("第一章", "h2", ["正文"], 1))
    assert "<title>第一章</title>" in xhtml
    assert "<p>正文</p>" in xhtml


def test_rule_analyzer_suggests_chapter_rule() -> None:
    lines = ["第一章 起始", "正文"]
    suggestions = RuleAnalyzer().suggest(lines)
    assert any(item.level == "h2" for item in suggestions)


def test_rule_analyzer_suggests_english_chapter_rule() -> None:
    lines = ["CHAPTER 12", "Body text"]
    suggestions = RuleAnalyzer().suggest(lines)
    assert any(item.level == "h2" and "English Chapter" in item.name for item in suggestions)


def test_rule_analyzer_suggests_english_volume_rule() -> None:
    lines = ["PART II", "CHAPTER 1", "Body text"]
    suggestions = RuleAnalyzer().suggest(lines)
    assert any(item.level == "h1" and "English Volume" in item.name for item in suggestions)


def test_rule_analyzer_can_keep_two_rules_per_level() -> None:
    presets = [
        {"name": "chapter_a", "pattern": r"^Chapter\s+\d+.*$", "level": "h2"},
        {"name": "chapter_b", "pattern": r"^CHAPTER\s+\d+.*$", "level": "h2"},
        {"name": "chapter_c", "pattern": r"^第[零一二三四五六七八九十百千万两〇0-9０-９]+章.*$", "level": "h2"},
    ]
    lines = ["CHAPTER 1", "Chapter 2", "第3章 标题", "Body text"]
    suggestions = RuleAnalyzer.from_preset_items(presets).suggest(
        lines, max_rules_per_level=2
    )
    assert sum(1 for item in suggestions if item.level == "h2") == 2


def test_paragraph_renderer_wraps_each_line() -> None:
    rendered = ParagraphRenderer.render("第一行\n第二行\n\n第三行", indent="  ")
    assert rendered.count("<p>") == 3
    assert "  <p>第一行</p>" in rendered
    assert "  <p>第二行</p>" in rendered
    assert "  <p>第三行</p>" in rendered


def test_paragraph_renderer_keeps_heading_line_without_p() -> None:
    rendered = ParagraphRenderer.render("<h2>第一章</h2>\n正文", indent="  ")
    assert "  <h2>第一章</h2>" in rendered
    assert "<p><h2>第一章</h2></p>" not in rendered


def test_document_preprocess_removes_empty_lines() -> None:
    raw = "第一行\n\n   \n第二行"
    processed = DocumentLoader.preprocess_text(raw, remove_empty_lines=True, strip_indent=False)
    assert processed == "第一行\n第二行"


def test_document_preprocess_strips_paragraph_indent() -> None:
    raw = "    第一段\n\t第二段\n　　第三段"
    processed = DocumentLoader.preprocess_text(raw, remove_empty_lines=False, strip_indent=True)
    assert processed == "第一段\n第二段\n第三段"


def test_configuration_saves_nested_ui_state_as_valid_toml(tmp_path) -> None:
    path = tmp_path / "config.toml"
    config = ConfigurationManager.default_config()
    config["ui"]["window_state"] = {
        "x": 10,
        "y": 20,
        "width": 885,
        "height": 585,
        "maximized": False,
    }

    ConfigurationManager.save(path, config)
    loaded = ConfigurationManager.load(path)

    assert loaded["ui"]["window_state"]["width"] == 885
    assert loaded["ui"]["window_state"]["maximized"] is False

