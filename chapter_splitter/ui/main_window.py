from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from chapter_splitter import __version__
from chapter_splitter.resources import register_icons_resource
from chapter_splitter.ui.common import t
from chapter_splitter.ui.dialogs import (
    PresetRulesEditorDialog,
    TemplateEditorDialog,
    TextPreprocessDialog,
)
from chapter_splitter.ui.main_window_icons import apply_main_window_icons
from chapter_splitter.ui.main_window_layout import build_main_window_layout
from chapter_splitter.ui.main_window_texts import retranslate_main_window
from chapter_splitter.ui.widgets import RegexRow


class MainWindow(QtWidgets.QMainWindow):
    _DEFAULT_WIDTH = 1200
    _DEFAULT_HEIGHT = 560
    _MIN_RESTORED_WIDTH = 720
    _MIN_RESTORED_HEIGHT = 480
    _PROJECT_GITHUB_URL = "https://github.com/hypsoma/chapter-splitter-sigil"
    _PROJECT_AUTHOR = "hypsoma"
    _PROJECT_EMAIL = "N/A"

    load_clicked = QtCore.Signal()
    preprocess_clicked = QtCore.Signal()
    analyze_clicked = QtCore.Signal()
    preview_clicked = QtCore.Signal()
    sequence_check_clicked = QtCore.Signal()
    split_clicked = QtCore.Signal()
    language_changed = QtCore.Signal(str)
    edit_preset_clicked = QtCore.Signal()
    closing = QtCore.Signal()

    def __init__(self, sigil_mode: bool = False) -> None:
        super().__init__()
        register_icons_resource()
        self.setWindowTitle(t("分章助手"))
        self.resize(self._DEFAULT_WIDTH, self._DEFAULT_HEIGHT)
        self.setAcceptDrops(True)
        self._sigil_mode = sigil_mode
        self._restore_maximized = False

        self._regex_rows: list[RegexRow] = []
        self._default_template_text = ""

        build_main_window_layout(self)

        self.preprocess_btn.clicked.connect(self.preprocess_clicked)
        self.analyze_btn.clicked.connect(self.analyze_clicked)
        self.preview_btn.clicked.connect(self.preview_clicked)
        self.sequence_check_btn.clicked.connect(self.sequence_check_clicked)
        self.split_btn.clicked.connect(self.split_clicked)
        self.edit_template_btn.clicked.connect(self.open_template_editor)
        self.add_preset_btn.clicked.connect(self.edit_preset_clicked)
        self.info_btn.clicked.connect(self.show_about_dialog)
        self._apply_icons()

    def choose_input_file(self, initial_dir: str | Path | None = None) -> str:
        dialog = QtWidgets.QFileDialog(
            self,
            t("选择文本"),
            self._input_dialog_directory(initial_dir),
            t("文本文件 (*.txt);;所有文件 (*)"),
        )
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog, False)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return ""
        files = dialog.selectedFiles()
        return files[0] if files else ""

    def _input_dialog_directory(self, initial_dir: str | Path | None = None) -> str:
        for candidate in (
            initial_dir,
            self.input_path_edit.text().strip(),
            Path.home(),
        ):
            if not candidate:
                continue
            path = Path(candidate).expanduser()
            if path.is_file():
                return str(path.parent)
            if path.is_dir():
                return str(path)
        return ""

    def choose_output_dir(self) -> str:
        dialog = QtWidgets.QFileDialog(self, t("选择输出"))
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        dialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly, True)
        dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog, False)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return ""
        files = dialog.selectedFiles()
        return files[0] if files else ""

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def show_error(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, t("错误"), message)

    def show_info(self, message: str) -> None:
        QtWidgets.QMessageBox.information(self, t("提示"), message)

    def show_about_dialog(self) -> None:
        message = (
            f"{t('版本')}: {__version__}\n"
            f"{t('GitHub')}: {self._PROJECT_GITHUB_URL}\n"
            f"{t('作者')}: {self._PROJECT_AUTHOR}\n"
            # f"{t('邮箱')}: {self._PROJECT_EMAIL}"
        )
        QtWidgets.QMessageBox.information(self, t("关于"), message)

    def set_default_template(self, template_text: str) -> None:
        self._default_template_text = template_text

    def get_default_template(self) -> str:
        return self._default_template_text

    def restore_window_state(self, state: object) -> None:
        if not isinstance(state, dict):
            return

        width = self._config_int(state.get("width"))
        height = self._config_int(state.get("height"))
        if (
            width is None
            or height is None
            or width < self._MIN_RESTORED_WIDTH
            or height < self._MIN_RESTORED_HEIGHT
        ):
            return

        x = self._config_int(state.get("x"))
        y = self._config_int(state.get("y"))
        if x is not None and y is not None:
            self.setGeometry(x, y, width, height)
        else:
            self.resize(width, height)
        self._restore_maximized = bool(state.get("maximized", False))

    def current_window_state(self) -> dict[str, int | bool]:
        geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        return {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
            "maximized": self.isMaximized(),
        }

    @staticmethod
    def _config_int(value: object) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def open_template_editor(self) -> None:
        dialog = TemplateEditorDialog(self._default_template_text, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._default_template_text = dialog.template_text()

    def add_regex_row(self) -> RegexRow:
        row = RegexRow()
        row.remove_clicked.connect(self.remove_regex_row)
        self._regex_rows.append(row)
        self.regex_container.insertWidget(max(0, self.regex_container.count() - 1), row)
        row.retranslate_texts()
        return row

    def remove_regex_row(self, row: RegexRow) -> None:
        if row in self._regex_rows:
            self._regex_rows.remove(row)
        self.regex_container.removeWidget(row)
        row.setParent(None)
        row.deleteLater()

    def regex_rows(self) -> list[RegexRow]:
        return list(self._regex_rows)

    def regex_row_count(self) -> int:
        return len(self._regex_rows)

    def clear_regex_rows(self) -> None:
        for row in list(self._regex_rows):
            self.regex_container.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._regex_rows.clear()

    def context_menu(self, position: QtCore.QPoint) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(self)
        menu.addAction(t("复制标题"))
        return menu

    @staticmethod
    def selected_indexes(tree: QtWidgets.QTreeView) -> list[QtCore.QModelIndex]:
        if not tree.selectionModel():
            return []
        return tree.selectionModel().selectedRows(0)

    @staticmethod
    def copy_to_clipboard(text: str) -> None:
        QtGui.QGuiApplication.clipboard().setText(text)

    def _build_preview_filter_menu(self) -> None:
        self.preview_filter_menu = QtWidgets.QMenu(self)
        self.preview_filter_level_menu = self.preview_filter_menu.addMenu(t("按级别"))
        self.preview_filter_level_actions: dict[str, QtGui.QAction] = {}
        for level in ("h1", "h2", "h3", "h4", "h5", "h6"):
            action = self.preview_filter_level_menu.addAction(level.upper())
            action.setCheckable(True)
            action.setChecked(True)
            self.preview_filter_level_actions[level] = action
        self.preview_filter_menu.addSeparator()
        self.preview_filter_include_ignored_action = self.preview_filter_menu.addAction(t("显示已忽略章节"))
        self.preview_filter_include_ignored_action.setCheckable(True)
        self.preview_filter_include_ignored_action.setChecked(True)
        self.preview_filter_problems_only_action = self.preview_filter_menu.addAction(t("仅显示问题章节"))
        self.preview_filter_problems_only_action.setCheckable(True)
        self.preview_filter_problems_only_action.setChecked(False)
        self.preview_filter_menu.addSeparator()
        self.preview_filter_reset_action = self.preview_filter_menu.addAction(t("重置筛选"))

    def _open_preview_filter_menu(self) -> None:
        anchor = self.preview_filter_btn.mapToGlobal(QtCore.QPoint(0, self.preview_filter_btn.height()))
        self.preview_filter_menu.exec(anchor)

    def _apply_icons(self) -> None:
        apply_main_window_icons(self)

    def apply_preview_column_layout(self) -> None:
        viewport_width = max(0, self.preview_tree.viewport().width())
        if viewport_width <= 0:
            return

        side_column_ratio = 0.12
        min_side_column_width = 64
        level_width = max(min_side_column_width, int(viewport_width * side_column_ratio))
        ignore_width = max(min_side_column_width, int(viewport_width * side_column_ratio))
        title_width = max(200, viewport_width - level_width - ignore_width)

        self.preview_tree.setColumnWidth(0, title_width)
        self.preview_tree.setColumnWidth(1, level_width)
        self.preview_tree.setColumnWidth(2, ignore_width)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.apply_preview_column_layout()

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        if self._restore_maximized:
            self._restore_maximized = False
            QtCore.QTimer.singleShot(0, self.showMaximized)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() in {
            QtCore.QEvent.Type.PaletteChange,
            QtCore.QEvent.Type.ApplicationPaletteChange,
        }:
            self._apply_icons()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.closing.emit()
        super().closeEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        # Avoid reading URL content here — on Wayland, accessing MIME
        # data during dragEnter triggers a synchronous pipe read that
        # times out.  Filter by extension in dropEvent instead.
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".txt"):
                self.input_path_edit.setText(path)
                self.load_clicked.emit()
                event.acceptProposedAction()
                return
        event.ignore()

    def set_language_mode(self, mode: str) -> None:
        mapping = {"auto": t("跟随系统"), "zh": "EN", "en": "中文"}
        self.language_btn.setText(mapping.get(mode, t("跟随系统")))

    def retranslate_ui(self) -> None:
        retranslate_main_window(self)

    def open_preset_rules_editor(
        self,
        presets: list[dict[str, str]],
        builtin_presets: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]] | None:
        dialog = PresetRulesEditorDialog(presets, builtin_presets, self)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        return dialog.presets()

    def open_text_preprocess_dialog(
        self, remove_empty_lines: bool, strip_paragraph_indent: bool
    ) -> dict[str, bool] | None:
        dialog = TextPreprocessDialog(remove_empty_lines, strip_paragraph_indent, self)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return None
        return dialog.options()
