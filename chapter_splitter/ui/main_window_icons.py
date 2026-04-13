from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from chapter_splitter.ui.common import themed_icon

if TYPE_CHECKING:
    from chapter_splitter.ui.main_window import MainWindow


def apply_main_window_icons(window: MainWindow) -> None:
    small_icon_size = max(
        16, window.style().pixelMetric(QtWidgets.QStyle.PixelMetric.PM_SmallIconSize)
    )
    window.preprocess_btn.setIcon(themed_icon(window, "broom", small_icon_size))
    window.analyze_btn.setIcon(themed_icon(window, "search", small_icon_size))
    window.preview_btn.setIcon(themed_icon(window, "eye", small_icon_size))
    window.sequence_check_btn.setIcon(
        themed_icon(window, "excalmation-triangel", small_icon_size)
    )
    window.split_btn.setIcon(themed_icon(window, "cogs", small_icon_size))
    window.add_rule_btn.setIcon(themed_icon(window, "plus", small_icon_size))
    window.clear_rule_btn.setIcon(themed_icon(window, "trash", small_icon_size))
    window.expand_btn.setIcon(
        themed_icon(window, "angle-double-down", small_icon_size)
    )
    window.collapse_btn.setIcon(themed_icon(window, "angle-double-up", small_icon_size))
    window.edit_template_btn.setIcon(themed_icon(window, "code", small_icon_size))
    window.language_btn.setIcon(
        themed_icon(window, "language", window.language_btn.iconSize().width())
    )
    window.info_btn.setIcon(themed_icon(window, "info", window.info_btn.iconSize().width()))
    window.add_preset_btn.setIcon(themed_icon(window, "magic", small_icon_size))
    window.preview_filter_btn.setIcon(themed_icon(window, "filter", small_icon_size))
