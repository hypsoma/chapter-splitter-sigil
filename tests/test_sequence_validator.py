from chapter_splitter.domain.models import ChapterSegment
from chapter_splitter.domain.sequence_validator import SequenceValidator


def test_sequence_isolated_by_level() -> None:
    segments = [
        ChapterSegment("第一卷 归来", "h1", "a", 1),
        ChapterSegment("第一章 风起", "h2", "a", 2),
        ChapterSegment("第二章 云涌", "h2", "a", 3),
    ]
    preview = SequenceValidator().build_preview(segments)
    assert preview[1].sequence_warning is None
    assert preview[2].sequence_warning is None


def test_extract_number_supports_chinese_digits_style() -> None:
    validator = SequenceValidator()
    assert validator.extract_number("二〇二六年 特别篇") == 2026


def test_volume_reset_clears_chapter_tracking() -> None:
    """Chapters restarting at 1 under a new volume should not trigger warnings."""
    segments = [
        ChapterSegment("第一卷 序章", "h1", "a", 1),
        ChapterSegment("第一章 初遇", "h2", "a", 2),
        ChapterSegment("第二章 重逢", "h2", "a", 3),
        ChapterSegment("第二卷 归来", "h1", "a", 4),
        ChapterSegment("第一章 再起", "h2", "a", 5),
        ChapterSegment("第二章 征程", "h2", "a", 6),
    ]
    preview = SequenceValidator().build_preview(segments)
    for entry in preview:
        assert entry.sequence_warning is None, (
            f"Unexpected warning on '{entry.title}': {entry.sequence_warning}"
        )


def test_gap_detected_between_chapters() -> None:
    """A missing chapter (3 -> 5) should flag the later entry as a gap."""
    segments = [
        ChapterSegment("第一章 开端", "h2", "a", 1),
        ChapterSegment("第二章 发展", "h2", "a", 2),
        ChapterSegment("第三章 高潮", "h2", "a", 3),
        ChapterSegment("第五章 结局", "h2", "a", 4),
        ChapterSegment("第六章 尾声", "h2", "a", 5),
    ]
    preview = SequenceValidator().build_preview(segments)
    assert preview[0].sequence_warning is None
    assert preview[1].sequence_warning is None
    assert preview[2].sequence_warning is None
    assert preview[3].sequence_warning is not None
    assert "跳章" in preview[3].sequence_warning
    assert preview[4].sequence_warning is None


def test_anomaly_detected_for_misplaced_chapter() -> None:
    """A chapter that doesn't connect to either neighbor is an anomaly."""
    segments = [
        ChapterSegment("第一章 开端", "h2", "a", 1),
        ChapterSegment("第二章 发展", "h2", "a", 2),
        ChapterSegment("第十章 乱入", "h2", "a", 3),
        ChapterSegment("第四章 继续", "h2", "a", 4),
        ChapterSegment("第五章 结局", "h2", "a", 5),
    ]
    preview = SequenceValidator().build_preview(segments)
    assert preview[0].sequence_warning is None
    assert preview[1].sequence_warning is None
    assert preview[2].sequence_warning is not None
    assert "编号异常" in preview[2].sequence_warning
    # Chapter 4 connects forward to 5, so it gets a gap warning (not anomaly)
    assert preview[3].sequence_warning is not None
    assert "跳章" in preview[3].sequence_warning
    assert preview[4].sequence_warning is None


def test_no_warnings_for_consecutive_sequence() -> None:
    segments = [
        ChapterSegment("第一章 风", "h2", "a", 1),
        ChapterSegment("第二章 林", "h2", "a", 2),
        ChapterSegment("第三章 火", "h2", "a", 3),
        ChapterSegment("第四章 山", "h2", "a", 4),
    ]
    preview = SequenceValidator().build_preview(segments)
    for entry in preview:
        assert entry.sequence_warning is None
