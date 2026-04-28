from chapter_splitter.domain.models import ChapterSegment
from chapter_splitter.domain.name_generator import NameGenerator


def test_relative_counter_resets_after_parent_change() -> None:
    rules = {
        "h1": "{000}_{title}",
        "h2": "{h1}_{$$$}_{title}",
    }
    generator = NameGenerator(rules)

    _ = generator.next(ChapterSegment("第一卷 归来", "h1", ["a"], 1))
    first_h2 = generator.next(ChapterSegment("第一章 风起", "h2", ["a"], 2))
    second_h2 = generator.next(ChapterSegment("第二章 云涌", "h2", ["a"], 3))
    _ = generator.next(ChapterSegment("第二卷 远行", "h1", ["a"], 4))
    reset_h2 = generator.next(ChapterSegment("第一章 重启", "h2", ["a"], 5))

    assert "_001_" in first_h2
    assert "_002_" in second_h2
    assert "_001_" in reset_h2


def test_fixed_width_level_counters() -> None:
    rules = {
        "h1": "Vol{h1_no3}",
        "h2": "Vol{h1_no3}_Chapter{h2_no3}",
    }
    generator = NameGenerator(rules)

    vol = generator.next(ChapterSegment("第一卷", "h1", ["a"], 1))
    chapter = generator.next(ChapterSegment("第一章", "h2", ["a"], 2))

    assert vol == "Vol001.xhtml"
    assert chapter == "Vol001_Chapter001.xhtml"


def test_two_digit_level_counters() -> None:
    rules = {
        "h1": "Juan-{h1_no2}",
        "h2": "Juan{h1_no2}{h2_no2}",
    }
    generator = NameGenerator(rules)

    volume = generator.next(ChapterSegment("第一卷", "h1", ["a"], 1))
    chapter = generator.next(ChapterSegment("第一章", "h2", ["a"], 2))

    assert volume == "Juan-01.xhtml"
    assert chapter == "Juan0101.xhtml"
