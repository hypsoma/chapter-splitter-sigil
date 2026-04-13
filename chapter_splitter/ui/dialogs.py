from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from chapter_splitter.ui.common import t


class SequenceReportDialog(QtWidgets.QDialog):
    """Dialog listing sequence break warnings with clickable navigation."""

    locate_requested = QtCore.Signal(int)

    def __init__(
        self,
        warnings: list[tuple[int, str, str]],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("断章检查报告"))
        self.resize(640, 420)
        self._warnings = warnings

        layout = QtWidgets.QVBoxLayout(self)
        self._list = QtWidgets.QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setStyleSheet(
            "QListWidget::item { min-height: 30px; padding: 4px 8px; }"
        )

        for idx, title, warning in warnings:
            display = f"⚠ #{idx + 1}「{title}」— {warning}"
            item = QtWidgets.QListWidgetItem(display)
            item.setData(QtCore.Qt.UserRole, idx)
            self._list.addItem(item)

        layout.addWidget(self._list, 1)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Close
        )
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        entry_index = item.data(QtCore.Qt.UserRole)
        if entry_index is not None:
            self.locate_requested.emit(int(entry_index))


class TemplateEditorDialog(QtWidgets.QDialog):
    def __init__(
        self, template_text: str, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("编辑全局模板"))
        self.resize(820, 620)

        layout = QtWidgets.QVBoxLayout(self)
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setPlainText(template_text)
        layout.addWidget(self.editor, 1)

        bottom_row = QtWidgets.QHBoxLayout()
        help_btn = QtWidgets.QPushButton("?")
        help_btn.setFixedSize(28, 28)
        help_btn.setToolTip(t("查看模板占位符说明"))
        help_btn.clicked.connect(self._show_help)
        bottom_row.addWidget(help_btn)
        bottom_row.addStretch(1)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        bottom_row.addWidget(button_box)
        layout.addLayout(bottom_row)

    def template_text(self) -> str:
        return self.editor.toPlainText()

    def _show_help(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            t("模板占位符说明"),
            t(
                "[TITLE]\n"
                "替换为章节标题文本，出现在 <title> 标签中，\n"
                "用于阅读器显示章节名称。\n\n"
                "[MAIN]\n"
                "替换为章节正文内容（包含标题标签和段落），\n"
                "出现在 <body> 内部，是实际的阅读内容区域。\n\n"
                "模板中必须包含这两个占位符，否则输出文件\n"
                "将缺少标题或正文。"
            ),
        )


class TextPreprocessDialog(QtWidgets.QDialog):
    def __init__(
        self,
        remove_empty_lines: bool,
        strip_paragraph_indent: bool,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("txt预处理"))
        self.setMinimumWidth(360)

        layout = QtWidgets.QVBoxLayout(self)
        self.remove_empty_lines_check = QtWidgets.QCheckBox(t("去除空行"))
        self.remove_empty_lines_check.setChecked(remove_empty_lines)
        self.strip_indent_check = QtWidgets.QCheckBox(t("去除段前缩进"))
        self.strip_indent_check.setChecked(strip_paragraph_indent)
        layout.addWidget(self.remove_empty_lines_check)
        layout.addWidget(self.strip_indent_check)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def options(self) -> dict[str, bool]:
        return {
            "remove_empty_lines": self.remove_empty_lines_check.isChecked(),
            "strip_paragraph_indent": self.strip_indent_check.isChecked(),
        }


class PresetRulesEditorDialog(QtWidgets.QDialog):
    def __init__(
        self,
        presets: list[dict[str, str]],
        builtin_presets: list[dict[str, str]] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("编辑预设规则"))
        self.resize(900, 560)
        self._builtin_presets = list(builtin_presets or [])

        layout = QtWidgets.QVBoxLayout(self)
        toolbar = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton(t("新增"))
        self.delete_btn = QtWidgets.QPushButton(t("删除"))
        self.reset_builtin_btn = QtWidgets.QPushButton(t("重置"))
        self.reset_builtin_btn.setToolTip(t("清空当前列表并恢复默认内置预设"))
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.reset_builtin_btn)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            [t("规则名称"), t("正则规则"), t("标题级别")]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        layout.addWidget(self.table, 1)

        for item in presets:
            self._append_row(
                str(item.get("name", "")),
                str(item.get("pattern", "")),
                str(item.get("level", "h2")),
                str(item.get("name_key", "")).strip(),
            )

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.add_btn.clicked.connect(lambda: self._append_row("", "", "h2", ""))
        self.delete_btn.clicked.connect(self._delete_selected)
        self.reset_builtin_btn.clicked.connect(self._reset_builtin_presets)

    def _append_row(self, name: str, pattern: str, level: str, name_key: str) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        name_item = QtWidgets.QTableWidgetItem(name)
        name_item.setData(QtCore.Qt.UserRole, name_key)
        self.table.setItem(row, 0, name_item)
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(pattern))
        level_combo = QtWidgets.QComboBox()
        level_combo.addItems(["h1", "h2", "h3", "h4", "h5", "h6"])
        level_combo.setCurrentText(
            level if level in {"h1", "h2", "h3", "h4", "h5", "h6"} else "h2"
        )
        self.table.setCellWidget(row, 2, level_combo)

    def _delete_selected(self) -> None:
        rows = sorted(
            {index.row() for index in self.table.selectedIndexes()}, reverse=True
        )
        for row in rows:
            self.table.removeRow(row)

    def _reset_builtin_presets(self) -> None:
        self.table.setRowCount(0)
        for item in self._builtin_presets:
            self._append_row(
                str(item.get("name", "")),
                str(item.get("pattern", "")),
                str(item.get("level", "h2")),
                str(item.get("name_key", "")).strip(),
            )

    def presets(self) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            pattern_item = self.table.item(row, 1)
            level_widget = self.table.cellWidget(row, 2)
            name = (name_item.text() if name_item else "").strip()
            name_key = (
                str(name_item.data(QtCore.Qt.UserRole)).strip()
                if name_item is not None
                else ""
            )
            pattern = (pattern_item.text() if pattern_item else "").strip()
            if not pattern:
                continue
            level = (
                level_widget.currentText()
                if isinstance(level_widget, QtWidgets.QComboBox)
                else "h2"
            )
            preset = {"name": name or t("自定义预设"), "pattern": pattern, "level": level}
            if name_key:
                preset["name_key"] = name_key
            results.append(preset)
        return results
