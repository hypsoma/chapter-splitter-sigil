from __future__ import annotations

import copy
from pathlib import Path
from typing import Callable

from PySide6 import QtCore, QtWidgets

from chapter_splitter.domain.models import ChapterSegment, PreviewEntry

from chapter_splitter.domain.document_loader import DocumentLoader
from chapter_splitter.domain.preset_catalog import (
    BUILTIN_PRESET_BY_KEY,
    NAME_KEY_LABEL,
    PRESET_NAME_KEY_ORDER,
)
from chapter_splitter.domain.rule_analyzer import RuleAnalyzer
from chapter_splitter.infrastructure.configuration import (
    DEFAULT_AUTO_ANALYZE_MAX_RULES_PER_LEVEL,
    DEFAULT_CUSTOM_PRESETS,
    DEFAULT_ENABLED_BUILTIN_PRESET_KEYS,
    DEFAULT_LAST_INPUT_DIR,
    DEFAULT_LONG_TITLE_THRESHOLD,
    DEFAULT_MAX_REGEX,
    DEFAULT_NAME_RULES,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REMOVE_EMPTY_LINES,
    DEFAULT_STRIP_PARAGRAPH_INDENT,
    DEFAULT_UI_LANGUAGE,
    SUPPORTED_UI_LANGUAGES,
    ConfigurationManager,
)
from chapter_splitter.ui.i18n import AppTranslator, select_language
from chapter_splitter.ui.preview_model import PreviewFilterProxyModel, PreviewTreeModel
from chapter_splitter.ui.view import MainWindow, SequenceReportDialog, t
from chapter_splitter.ui.workers import LoadTextJob, SplitJob


class MainPresenter(QtCore.QObject):
    _BUILTIN_PRESET_BY_KEY = BUILTIN_PRESET_BY_KEY
    _PRESET_NAME_KEY_ORDER = PRESET_NAME_KEY_ORDER
    _NAME_KEY_LABEL = NAME_KEY_LABEL

    def __init__(
        self,
        view: MainWindow,
        config_path: Path,
        output_writer: Callable[[str, str], None] | None = None,
        sigil_mode: bool = False,
        latest_export_name_provider: Callable[[], str] | None = None,
    ) -> None:
        super().__init__()
        self._view = view
        self._config_path = config_path
        self._output_writer = output_writer
        self._sigil_mode = sigil_mode
        self._latest_export_name_provider = latest_export_name_provider
        self._config = ConfigurationManager.load(config_path)
        self._persisted_rules = copy.deepcopy(self._config.get("rules", []))
        self._loaded_text: str = ""
        self._preprocess_options = {
            "remove_empty_lines": DEFAULT_REMOVE_EMPTY_LINES,
            "strip_paragraph_indent": DEFAULT_STRIP_PARAGRAPH_INDENT,
        }
        self._pool = QtCore.QThreadPool(self)
        self._active_jobs = {}
        self._is_shutting_down = False
        self._preset_items = self._build_preset_items()
        self._segments: list[ChapterSegment] = []
        self._available_preview_levels: set[str] = {"h1", "h2", "h3", "h4", "h5", "h6"}

        threshold = int(
            self._config.get("ui", {}).get(
                "long_title_threshold", DEFAULT_LONG_TITLE_THRESHOLD
            )
        )
        self._model = PreviewTreeModel(long_title_threshold=threshold)
        self._proxy_model = PreviewFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        self._view.preview_tree.setModel(self._proxy_model)
        self._view.apply_preview_column_layout()

        self._bind_events()
        self._load_settings_to_view()

    def _bind_events(self) -> None:
        self._view.pick_input_btn.clicked.connect(self._pick_input)
        self._view.pick_output_btn.clicked.connect(self._pick_output)
        self._view.load_clicked.connect(self.load_text)
        self._view.preprocess_clicked.connect(self._edit_text_preprocess)
        self._view.analyze_clicked.connect(self.auto_analyze_rules)
        self._view.preview_clicked.connect(self.preview)
        self._view.sequence_check_clicked.connect(self._check_sequence)
        self._view.split_clicked.connect(self.split)
        self._view.add_rule_btn.clicked.connect(self._add_empty_rule)
        self._view.clear_rule_btn.clicked.connect(self._clear_rules)
        self._view.edit_preset_clicked.connect(self._edit_preset_rules)
        self._view.language_changed.connect(self._on_language_changed)
        self._view.long_title_threshold_spin.valueChanged.connect(
            self._on_threshold_changed
        )
        self._view.expand_btn.clicked.connect(self._view.preview_tree.expandAll)
        self._view.collapse_btn.clicked.connect(self._view.preview_tree.collapseAll)
        self._view.preview_search_edit.textChanged.connect(
            self._on_preview_search_changed
        )
        for action in self._view.preview_filter_level_actions.values():
            action.triggered.connect(self._on_preview_filter_changed)
        self._view.preview_filter_include_ignored_action.triggered.connect(
            self._on_preview_filter_changed
        )
        self._view.preview_filter_problems_only_action.triggered.connect(
            self._on_preview_filter_changed
        )
        self._view.preview_filter_reset_action.triggered.connect(
            self._reset_preview_filter
        )
        self._view.preview_tree.customContextMenuRequested.connect(
            self._copy_title_from_menu
        )
        self._view.preview_tree.doubleClicked.connect(self._edit_title_on_double_click)
        self._view.preview_tree.clicked.connect(self._on_tree_clicked)
        self._view.closing.connect(self._on_view_closing)

    def _load_settings_to_view(self) -> None:
        self._view.clear_regex_rows()
        rules = self._config.get("rules", [])
        for rule in rules:
            row = self._view.add_regex_row()
            row.set_preset_options(self._preset_items)
            row.name_edit.setText(self._display_rule_name(rule))
            row.name_edit.setCursorPosition(0)
            row.set_pattern_text(str(rule.get("pattern", "")))
            if row.pattern_combo.lineEdit() is not None:
                row.pattern_combo.lineEdit().setCursorPosition(0)
            row.level_combo.setCurrentText(str(rule.get("level", "h2")))
            row.split_check.setChecked(bool(rule.get("split", True)))

        templates = self._config.get("templates", {})
        self._view.set_default_template(str(templates.get("default", "")))

        name_rules = self._config.get("name_rules", {})
        self._view.h1_name_rule_edit.setText(
            str(name_rules.get("h1", DEFAULT_NAME_RULES["h1"]))
        )
        self._view.h2_name_rule_edit.setText(
            str(name_rules.get("h2", DEFAULT_NAME_RULES["h2"]))
        )
        self._view.h3_name_rule_edit.setText(
            str(name_rules.get("h3", DEFAULT_NAME_RULES["h3"]))
        )

        ui_config = self._config.get("ui", {})
        self._preprocess_options["remove_empty_lines"] = bool(
            ui_config.get("remove_empty_lines", DEFAULT_REMOVE_EMPTY_LINES)
        )
        self._preprocess_options["strip_paragraph_indent"] = bool(
            ui_config.get("strip_paragraph_indent", DEFAULT_STRIP_PARAGRAPH_INDENT)
        )
        self._view.long_title_threshold_spin.setValue(
            int(ui_config.get("long_title_threshold", DEFAULT_LONG_TITLE_THRESHOLD))
        )
        self._view.input_path_edit.setText("")
        self._view.output_dir_edit.setText(DEFAULT_OUTPUT_DIR)
        self._view.set_language_mode(str(ui_config.get("language", DEFAULT_UI_LANGUAGE)))
        self._view.restore_window_state(ui_config.get("window_state"))

    def _collect_rules(self) -> list[dict[str, object]]:
        rules: list[dict[str, object]] = []
        for idx, widget in enumerate(self._view.regex_rows()):
            name = widget.name_edit.text().strip()
            pattern = widget.pattern_text()
            if not pattern:
                continue
            level = widget.level_combo.currentText()
            name_key = self._name_key_for_pattern_level(pattern, level)
            localized_default = self._label_for_name_key(name_key) if name_key else ""
            rules.append(
                {
                    **({"name_key": name_key} if name_key else {}),
                    **(
                        {"custom_name": name}
                        if name and (not localized_default or name != localized_default)
                        else {}
                    ),
                    "pattern": pattern,
                    "level": level,
                    "split": widget.split_check.isChecked(),
                    "priority": idx + 1,
                }
            )
        return rules

    def _build_preset_items(self) -> list[dict[str, str]]:
        language = self._ui_language()
        configured_keys = self._config.get("enabled_builtin_preset_keys")
        if isinstance(configured_keys, list):
            enabled_keys = [str(key).strip() for key in configured_keys if str(key).strip()]
        else:
            enabled_keys = list(DEFAULT_ENABLED_BUILTIN_PRESET_KEYS)
        items = self._build_builtin_preset_items(enabled_keys, language)

        configured_custom = self._config.get("custom_presets")
        custom_presets = (
            configured_custom if isinstance(configured_custom, list) else DEFAULT_CUSTOM_PRESETS
        )
        for preset in custom_presets:
            pattern = str(preset.get("pattern", "")).strip()
            if not pattern:
                continue
            items.append(
                {
                    "name": str(preset.get("name", "")).strip() or t("自定义预设"),
                    "pattern": pattern,
                    "level": str(preset.get("level", "h2")).strip() or "h2",
                }
            )
        return items

    def _build_builtin_preset_items(
        self,
        enabled_keys: list[str],
        language: str | None = None,
    ) -> list[dict[str, str]]:
        selected_language = language or self._ui_language()
        items: list[dict[str, str]] = []

        seen_keys: set[str] = set()
        for name_key in enabled_keys:
            if name_key in seen_keys:
                continue
            seen_keys.add(name_key)
            options = self._BUILTIN_PRESET_BY_KEY.get(name_key, {})
            selected = options.get(selected_language) or options.get("zh")
            if not selected:
                continue
            items.append(
                {
                    "name": self._label_for_name_key(name_key),
                    "name_key": name_key,
                    "pattern": selected["pattern"],
                    "level": selected["level"],
                }
            )
        return items

    def _name_key_for_pattern_level(self, pattern: str, level: str) -> str | None:
        for item in self._preset_items:
            if item["pattern"] == pattern and item["level"] == level:
                return item.get("name_key") or None
        return None

    def _display_rule_name(self, rule: dict[str, object]) -> str:
        custom_name = str(rule.get("custom_name", "")).strip()
        if custom_name:
            return custom_name

        name_key = str(rule.get("name_key", "")).strip()
        if name_key:
            return self._label_for_name_key(name_key)
        return ""

    def _ui_language(self) -> str:
        mode = str(
            self._config.get("ui", {}).get("language", DEFAULT_UI_LANGUAGE)
        ).lower()
        if mode in SUPPORTED_UI_LANGUAGES:
            return mode
        return select_language()

    def _label_for_name_key(self, name_key: str) -> str:
        labels = self._NAME_KEY_LABEL.get(name_key)
        if not labels:
            return name_key
        return labels.get(self._ui_language(), labels["zh"])

    def _sync_view_to_config(self) -> None:
        self._config["rules"] = self._collect_rules()
        self._config["templates"] = {
            "default": self._view.get_default_template().strip(),
        }
        self._config["name_rules"] = {
            "h1": self._view.h1_name_rule_edit.text().strip() or DEFAULT_NAME_RULES["h1"],
            "h2": self._view.h2_name_rule_edit.text().strip()
            or DEFAULT_NAME_RULES["h2"],
            "h3": self._view.h3_name_rule_edit.text().strip() or DEFAULT_NAME_RULES["h3"],
        }
        ui_config = dict(self._config.get("ui", {}))
        ui_config.update(
            {
                "max_regex": DEFAULT_MAX_REGEX,
                "auto_analyze_max_rules_per_level": int(
                    self._config.get("ui", {}).get(
                        "auto_analyze_max_rules_per_level",
                        DEFAULT_AUTO_ANALYZE_MAX_RULES_PER_LEVEL,
                    )
                ),
                "long_title_threshold": int(
                    self._view.long_title_threshold_spin.value()
                ),
                "remove_empty_lines": bool(
                    self._preprocess_options["remove_empty_lines"]
                ),
                "strip_paragraph_indent": bool(
                    self._preprocess_options["strip_paragraph_indent"]
                ),
                "language": str(
                    self._config.get("ui", {}).get("language", DEFAULT_UI_LANGUAGE)
                ),
                "window_state": self._view.current_window_state(),
            }
        )
        self._config["ui"] = ui_config
        self._save_config()
        self._model.set_long_title_threshold(
            int(self._config["ui"]["long_title_threshold"])
        )

    def _save_config(self) -> None:
        payload = copy.deepcopy(self._config)
        payload["rules"] = copy.deepcopy(self._persisted_rules)
        ConfigurationManager.save(self._config_path, payload)

    def _pick_input(self) -> None:
        chosen = self._view.choose_input_file(self._last_input_dir())
        if chosen:
            self._view.input_path_edit.setText(chosen)
            self._remember_input_dir(Path(chosen).parent)
            if self._should_use_input_scoped_default_output():
                self._view.output_dir_edit.setText(
                    str(Path(chosen).parent / DEFAULT_OUTPUT_DIR)
                )
            self.load_text()

    def _last_input_dir(self) -> str:
        configured = str(
            self._config.get("ui", {}).get("last_input_dir", DEFAULT_LAST_INPUT_DIR)
        ).strip()
        if configured:
            return configured

        current_input = self._view.input_path_edit.text().strip()
        if current_input:
            return str(Path(current_input).parent)
        return ""

    def _remember_input_dir(self, directory: Path) -> None:
        ui_config = self._config.setdefault("ui", {})
        ui_config["last_input_dir"] = str(directory)
        self._save_config()

    def _pick_output(self) -> None:
        chosen = self._view.choose_output_dir()
        if chosen:
            self._view.output_dir_edit.setText(chosen)

    def _should_use_input_scoped_default_output(self) -> bool:
        output_text = self._view.output_dir_edit.text().strip()
        return not output_text or output_text == DEFAULT_OUTPUT_DIR

    def _resolve_output_dir(self, source_text: str) -> Path:
        source_path = Path(source_text)
        output_text = self._view.output_dir_edit.text().strip()
        if not output_text or output_text == DEFAULT_OUTPUT_DIR:
            return source_path.parent / DEFAULT_OUTPUT_DIR
        return Path(output_text)

    @QtCore.Slot()
    def load_text(self) -> None:
        if self._is_shutting_down:
            return
        source = self._view.input_path_edit.text().strip()
        if not source:
            self._view.show_error(t("请先选择文本文件"))
            return

        self._view.set_status(t("后台读取文本中..."))
        job = LoadTextJob(Path(source))
        self._active_jobs[job.signals] = job
        job.signals.finished.connect(self._on_load_text_finished)
        job.signals.failed.connect(self._on_load_text_failed)
        self._pool.start(job)

    def _on_load_text_finished(self, text: str) -> None:
        if self._is_shutting_down:
            return
        self._active_jobs.pop(self.sender(), None)
        self._loaded_text = text
        self._view.set_status(
            t("已加载 {count} 行").format(count=len(text.splitlines()))
        )

    def _on_load_text_failed(self, error: str) -> None:
        if self._is_shutting_down:
            return
        self._active_jobs.pop(self.sender(), None)
        self._view.show_error(error)
        self._view.set_status(t("读取失败"))

    @QtCore.Slot()
    def auto_analyze_rules(self) -> None:
        if not self._loaded_text:
            self.load_text()
            return

        preprocessed = DocumentLoader.preprocess_text(
            self._loaded_text,
            remove_empty_lines=bool(self._preprocess_options["remove_empty_lines"]),
            strip_indent=bool(self._preprocess_options["strip_paragraph_indent"]),
        )
        max_rules_per_level = max(
            1,
            int(
                self._config.get("ui", {}).get(
                    "auto_analyze_max_rules_per_level",
                    DEFAULT_AUTO_ANALYZE_MAX_RULES_PER_LEVEL,
                )
            ),
        )
        suggestions = RuleAnalyzer.from_preset_items(self._preset_items).suggest(
            preprocessed.splitlines(),
            max_rules_per_level=max_rules_per_level,
        )
        if not suggestions:
            self._view.show_info(t("未识别到常见规则"))
            return

        self._view.clear_regex_rows()
        max_regex = int(
            self._config.get("ui", {}).get("max_regex", DEFAULT_MAX_REGEX)
        )
        for suggestion in suggestions[:max_regex]:
            row = self._view.add_regex_row()
            row.set_preset_options(self._preset_items)
            row.set_pattern_text(suggestion.pattern)
            row.level_combo.setCurrentText(suggestion.level)
            name_key = self._name_key_for_pattern_level(
                suggestion.pattern, suggestion.level
            )
            if name_key:
                row.name_edit.setText(self._label_for_name_key(name_key))
            else:
                row.name_edit.setText(t(suggestion.name))
            row.split_check.setChecked(True)
        self._view.set_status(
            t("自动分析完成，生成 {count} 条规则").format(count=len(suggestions))
        )

    @QtCore.Slot()
    def preview(self) -> None:
        if self._is_shutting_down:
            return
        source = self._view.input_path_edit.text().strip()
        if not source:
            self._view.show_error(t("请先选择文本文件"))
            return

        self._sync_view_to_config()
        job = SplitJob(
            input_path=Path(source),
            output_dir=self._resolve_output_dir(source),
            config=self._config,
            ignored_indices=self._model.ignored_indices(),
            write_output=False,
        )
        self._active_jobs[job.signals] = job
        job.signals.finished.connect(self._on_preview_finished)
        job.signals.failed.connect(self._on_split_failed)
        job.signals.progress.connect(self._on_preview_progress)
        self._pool.start(job)
        self._view.set_status(t("后台预览中..."))

    @QtCore.Slot()
    def split(self) -> None:
        if self._is_shutting_down:
            return
        source = self._view.input_path_edit.text().strip()
        if not source:
            self._view.show_error(t("请先选择文本文件"))
            return

        self._sync_view_to_config()
        job = SplitJob(
            input_path=Path(source),
            output_dir=self._resolve_output_dir(source),
            config=self._config,
            ignored_indices=self._model.ignored_indices(),
            write_output=self._output_writer is None,
            output_writer=self._output_writer,
        )
        self._active_jobs[job.signals] = job
        job.signals.finished.connect(self._on_split_finished)
        job.signals.failed.connect(self._on_split_failed)
        job.signals.progress.connect(self._on_split_progress)
        self._pool.start(job)
        self._view.set_status(t("后台分章中..."))

    def _on_preview_finished(self, result) -> None:
        if self._is_shutting_down:
            return
        self._active_jobs.pop(self.sender(), None)
        self._segments = result.segments
        self._model.set_entries(result.preview)
        self._apply_default_preview_filter(result.preview)
        self._view.apply_preview_column_layout()
        self._view.preview_tree.expandToDepth(1)
        self._view.set_status(
            t("预览完成，共 {count} 项").format(count=len(result.preview))
        )
        self._view.sequence_check_btn.setEnabled(True)

    def _on_split_finished(self, result) -> None:
        if self._is_shutting_down:
            return
        self._active_jobs.pop(self.sender(), None)
        self._segments = result.segments
        self._model.set_entries(result.preview)
        self._apply_default_preview_filter(result.preview)
        self._view.apply_preview_column_layout()
        self._view.preview_tree.expandToDepth(1)
        self._view.set_status(
            t("分章完成，输出 {count} 个文件").format(count=len(result.exported_files))
        )
        self._view.sequence_check_btn.setEnabled(True)
        if self._sigil_mode:
            QtWidgets.QMessageBox.information(
                self._view,
                t("完成"),
                t("已导入 {count} 个章节到 Sigil。").format(
                    count=len(result.exported_files)
                ),
            )
            self._view.close()

    def _on_split_failed(self, error: str) -> None:
        if self._is_shutting_down:
            return
        self._active_jobs.pop(self.sender(), None)
        self._view.show_error(error)
        self._view.set_status(t("执行失败"))

    def _on_preview_progress(self, done: int, total: int) -> None:
        if self._is_shutting_down:
            return
        self._view.set_status(
            t("后台预览中... {done}/{total}").format(done=done, total=total)
        )

    def _on_split_progress(self, done: int, total: int) -> None:
        if self._is_shutting_down:
            return
        if self._sigil_mode and self._latest_export_name_provider is not None:
            latest_name = self._latest_export_name_provider()
            if latest_name:
                self._view.set_status(
                    t("后台分章中... {done}/{total} | 正在导出：{name}").format(
                        done=done, total=total, name=latest_name
                    )
                )
                return
        self._view.set_status(
            t("后台分章中... {done}/{total}").format(done=done, total=total)
        )

    def _add_empty_rule(self) -> None:
        max_regex = int(
            self._config.get("ui", {}).get("max_regex", DEFAULT_MAX_REGEX)
        )
        if self._view.regex_row_count() >= max_regex:
            self._view.show_info(t("最多支持 {count} 条规则").format(count=max_regex))
            return
        row = self._view.add_regex_row()
        row.set_preset_options(self._preset_items)

    def _edit_preset_rules(self) -> None:
        builtin_defaults = self._build_builtin_preset_items(
            list(DEFAULT_ENABLED_BUILTIN_PRESET_KEYS)
        )
        edited = self._view.open_preset_rules_editor(self._preset_items, builtin_defaults)
        if edited is None:
            return
        enabled_keys: list[str] = []
        seen_enabled: set[str] = set()
        custom_presets: list[dict[str, str]] = []
        for preset in edited:
            name_key = str(preset.get("name_key", "")).strip()
            if name_key and name_key in self._BUILTIN_PRESET_BY_KEY:
                if name_key not in seen_enabled:
                    seen_enabled.add(name_key)
                    enabled_keys.append(name_key)
                continue

            pattern = str(preset.get("pattern", "")).strip()
            if not pattern:
                continue
            custom_presets.append(
                {
                    "name": str(preset.get("name", "")).strip() or t("自定义预设"),
                    "pattern": pattern,
                    "level": str(preset.get("level", "h2")).strip() or "h2",
                }
            )
        self._config["enabled_builtin_preset_keys"] = enabled_keys
        self._config["custom_presets"] = custom_presets
        self._preset_items = self._build_preset_items()
        for regex_row in self._view.regex_rows():
            regex_row.set_preset_options(self._preset_items)
        self._save_config()
        self._view.show_info(t("预设规则已更新"))

    def _check_sequence(self) -> None:
        warnings: list[tuple[int, str, str]] = []
        for node in self._model._flat:
            entry = node.entry
            if entry.sequence_warning:
                warnings.append((entry.index, entry.title, entry.sequence_warning))

        if not warnings:
            self._view.show_info(t("所有章节编号连续，未检测到断章"))
            return

        self._view.set_status(
            t("检测到 {count} 处断章问题").format(count=len(warnings))
        )
        dialog = SequenceReportDialog(warnings, self._view)
        dialog.locate_requested.connect(self._locate_entry_in_tree)
        dialog.show()

    def _locate_entry_in_tree(self, entry_index: int) -> None:
        for node in self._model._flat:
            if node.entry.index == entry_index:
                row = self._row_of_node(node)
                parent_index = self._parent_model_index(node)
                source_index = self._model.index(row, 0, parent_index)
                proxy_index = self._proxy_model.mapFromSource(source_index)
                if proxy_index.isValid():
                    self._view.preview_tree.scrollTo(
                        proxy_index,
                        QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter,
                    )
                    self._view.preview_tree.setCurrentIndex(proxy_index)
                return

    def _row_of_node(self, node) -> int:
        siblings = self._model._roots if node.parent is None else node.parent.children
        return siblings.index(node)

    def _parent_model_index(self, node) -> QtCore.QModelIndex:
        if node.parent is None:
            return QtCore.QModelIndex()
        parent_row = self._row_of_node(node.parent)
        grand_parent_index = self._parent_model_index(node.parent)
        return self._model.index(parent_row, 0, grand_parent_index)

    def _clear_rules(self) -> None:
        self._view.clear_regex_rows()

    def _copy_title_from_menu(self, position: QtCore.QPoint) -> None:
        menu = self._view.context_menu(position)
        action = menu.exec(self._view.preview_tree.viewport().mapToGlobal(position))
        if action is None:
            return

        clicked_proxy_index = self._view.preview_tree.indexAt(position)
        if not clicked_proxy_index.isValid():
            selected = self._view.selected_indexes(self._view.preview_tree)
            if not selected:
                return
            clicked_proxy_index = selected[0]

        source_index = self._proxy_model.mapToSource(clicked_proxy_index)
        title = self._model.title_from_index(source_index)
        if not title:
            return
        self._view.copy_to_clipboard(title)
        self._view.set_status(t("已复制标题"))

    def _edit_title_on_double_click(self, model_index: QtCore.QModelIndex) -> None:
        if model_index.column() != 0:
            return
        source_index = self._proxy_model.mapToSource(model_index)
        current_title = self._model.title_from_index(source_index)
        if not current_title:
            return
        edited_title, ok = QtWidgets.QInputDialog.getText(
            self._view,
            t("编辑标题"),
            t("新标题："),
            text=current_title,
        )
        if not ok:
            return
        if self._model.set_title(source_index, edited_title):
            self._view.set_status(t("标题已更新"))

    def _activate_level_editor_on_click(self, model_index: QtCore.QModelIndex) -> None:
        if model_index.column() != 1:
            return
        self._view.preview_tree.setCurrentIndex(model_index)
        QtCore.QTimer.singleShot(0, lambda: self._view.preview_tree.edit(model_index))

    def _on_tree_clicked(self, model_index: QtCore.QModelIndex) -> None:
        if model_index.column() == 1:
            self._activate_level_editor_on_click(model_index)
        self._show_body_preview(model_index)

    def _show_body_preview(self, model_index: QtCore.QModelIndex) -> None:
        source_index = self._proxy_model.mapToSource(model_index)
        if not source_index.isValid():
            return
        node = source_index.internalPointer()
        entry_index = node.entry.index
        if entry_index < 0 or entry_index >= len(self._segments):
            return
        body = self._segments[entry_index].body
        first_line = ""
        for line in body.splitlines():
            stripped = line.strip()
            # Skip heading tags (already shown as title)
            if stripped.startswith("<h") and stripped.endswith(">"):
                continue
            if stripped:
                first_line = stripped
                break
        label = self._view.body_preview_label
        text = first_line or t("（无正文内容）")
        max_width = self._view.preview_group.width()
        elided = label.fontMetrics().elidedText(
            text, QtCore.Qt.TextElideMode.ElideRight, max_width
        )
        label.setText(elided)

    def _on_preview_search_changed(self, keyword: str) -> None:
        self._proxy_model.set_title_keyword(keyword.strip())
        if keyword.strip():
            self._view.preview_tree.expandAll()

    def _on_preview_filter_changed(self, *_args) -> None:
        selected_levels = {
            level
            for level, action in self._view.preview_filter_level_actions.items()
            if action.isChecked()
        }
        if not selected_levels:
            fallback_action = self._view.preview_filter_level_actions["h1"]
            fallback_action.setChecked(True)
            selected_levels = {"h1"}

        self._proxy_model.set_visible_levels(selected_levels)
        self._proxy_model.set_show_ignored(
            self._view.preview_filter_include_ignored_action.isChecked()
        )
        self._proxy_model.set_problems_only(
            self._view.preview_filter_problems_only_action.isChecked()
        )
        if self._view.preview_search_edit.text().strip():
            self._view.preview_tree.expandAll()

    def _reset_preview_filter(self, *_args) -> None:
        for level, action in self._view.preview_filter_level_actions.items():
            action.setChecked(level in self._available_preview_levels)
        self._view.preview_filter_include_ignored_action.setChecked(True)
        self._view.preview_filter_problems_only_action.setChecked(False)
        self._on_preview_filter_changed()

    def _apply_default_preview_filter(self, entries: list[PreviewEntry]) -> None:
        available = {
            str(entry.level).strip().lower()
            for entry in entries
            if str(entry.level).strip().lower() in {"h1", "h2", "h3", "h4", "h5", "h6"}
        }
        if not available:
            available = {"h1", "h2", "h3", "h4", "h5", "h6"}
        self._available_preview_levels = available
        self._reset_preview_filter()

    def _on_threshold_changed(self, value: int) -> None:
        self._model.set_long_title_threshold(value)
        self._proxy_model.invalidateFilter()
        ui_config = self._config.setdefault("ui", {})
        ui_config["long_title_threshold"] = int(value)

    def _on_language_changed(self, mode: str) -> None:
        ui_config = self._config.setdefault("ui", {})
        ui_config["language"] = mode
        app = QtWidgets.QApplication.instance()
        active = mode if mode in SUPPORTED_UI_LANGUAGES else select_language()
        translator = AppTranslator(active)
        app.installTranslator(translator)
        app._app_translator = translator
        self._sync_builtin_rule_patterns_for_language(active)

        self._preset_items = self._build_preset_items()
        for row in self._view.regex_rows():
            row.set_preset_options(self._preset_items)

        self._view.retranslate_ui()
        self._view.set_language_mode(mode)
        self._model.headerDataChanged.emit(QtCore.Qt.Orientation.Horizontal, 0, 2)
        self._save_config()
        self._load_settings_to_view()
        self._view.show_info(t("语言已切换"))

    def _sync_builtin_rule_patterns_for_language(self, language: str) -> None:
        rules = self._config.get("rules", [])
        for rule in rules:
            name_key = str(rule.get("name_key", "")).strip()
            if not name_key:
                continue
            options = self._BUILTIN_PRESET_BY_KEY.get(name_key, {})
            selected = options.get(language) or options.get("zh")
            if not selected:
                continue
            rule["pattern"] = selected["pattern"]
            rule["level"] = selected["level"]

    def _edit_text_preprocess(self) -> None:
        edited = self._view.open_text_preprocess_dialog(
            remove_empty_lines=bool(self._preprocess_options["remove_empty_lines"]),
            strip_paragraph_indent=bool(
                self._preprocess_options["strip_paragraph_indent"]
            ),
        )
        if edited is None:
            return
        self._preprocess_options = edited
        self._sync_view_to_config()
        self._view.set_status(t("txt预处理设置已更新"))

    def _on_view_closing(self) -> None:
        self._sync_view_to_config()
        self._is_shutting_down = True
        for signals in list(self._active_jobs.keys()):
            for signal_name in ("finished", "failed", "progress"):
                signal = getattr(signals, signal_name, None)
                if signal is None:
                    continue
                try:
                    signal.disconnect()
                except (RuntimeError, TypeError):
                    pass
        self._active_jobs.clear()
        self._pool.clear()
        self._pool.waitForDone(3000)
