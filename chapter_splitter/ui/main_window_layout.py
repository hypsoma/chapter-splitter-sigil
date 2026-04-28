from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from chapter_splitter.infrastructure.configuration import (
    DEFAULT_LONG_TITLE_THRESHOLD,
    DEFAULT_MAX_REGEX,
    DEFAULT_OUTPUT_DIR,
)
from chapter_splitter.ui.common import t
from chapter_splitter.ui.widgets import (
    CenteredCheckStateDelegate,
    HeadingLevelDelegate,
    ProportionalPaddingHeaderView,
)

if TYPE_CHECKING:
    from chapter_splitter.ui.main_window import MainWindow


def build_main_window_layout(window: MainWindow) -> None:
    root = QtWidgets.QWidget()
    window.setCentralWidget(root)
    page_layout = QtWidgets.QVBoxLayout(root)
    page_layout.setSpacing(10)

    path_row = QtWidgets.QHBoxLayout()
    path_row.setSpacing(8)
    window.input_path_edit = QtWidgets.QLineEdit()
    window.input_path_edit.setPlaceholderText(
        t("请选择待分章的文本文件（支持拖拽 TXT）")
    )
    window.input_path_edit.setToolTip(t("输入或选择要处理的 TXT 文件路径"))
    window.output_dir_edit = QtWidgets.QLineEdit(DEFAULT_OUTPUT_DIR)
    window.output_dir_edit.setToolTip(t("分章结果输出目录"))
    window.pick_input_btn = QtWidgets.QPushButton(t("选择文本"))
    window.pick_input_btn.setToolTip(t("选择待处理的文本文件"))
    window.pick_output_btn = QtWidgets.QPushButton(t("选择输出"))
    window.pick_output_btn.setToolTip(t("选择分章结果输出目录"))
    row_min_height = 34
    button_fixed_width = 96
    window.input_path_edit.setMinimumHeight(row_min_height)
    window.output_dir_edit.setMinimumHeight(row_min_height)
    window.pick_input_btn.setMinimumHeight(row_min_height)
    window.pick_output_btn.setMinimumHeight(row_min_height)
    window.pick_input_btn.setFixedWidth(button_fixed_width)
    window.pick_output_btn.setFixedWidth(button_fixed_width)
    window.pick_input_btn.setStyleSheet("QPushButton { padding: 3px 8px; }")
    window.pick_output_btn.setStyleSheet("QPushButton { padding: 3px 8px; }")
    window.input_path_edit.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Expanding,
        QtWidgets.QSizePolicy.Policy.Fixed,
    )
    window.output_dir_edit.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Expanding,
        QtWidgets.QSizePolicy.Policy.Fixed,
    )
    window.pick_input_btn.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Fixed,
        QtWidgets.QSizePolicy.Policy.Fixed,
    )
    window.pick_output_btn.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Fixed,
        QtWidgets.QSizePolicy.Policy.Fixed,
    )
    path_row.addWidget(window.input_path_edit, 1)
    path_row.addWidget(window.pick_input_btn, 0)
    path_row.addWidget(window.output_dir_edit, 1)
    path_row.addWidget(window.pick_output_btn, 0)
    if window._sigil_mode:
        window.output_dir_edit.hide()
        window.pick_output_btn.hide()
    page_layout.addLayout(path_row)

    control_row = QtWidgets.QHBoxLayout()
    window.preprocess_btn = QtWidgets.QPushButton(t("txt预处理"))
    window.preprocess_btn.setToolTip(t("设置文本预处理规则：去除空行、去除段前缩进"))
    window.analyze_btn = QtWidgets.QPushButton(t("自动分析"))
    window.analyze_btn.setToolTip(t("根据文本内容自动识别常见章节正则"))
    window.preview_btn = QtWidgets.QPushButton(t("预览"))
    window.preview_btn.setToolTip(t("仅生成预览结构，不写入文件"))
    window.sequence_check_btn = QtWidgets.QPushButton(t("断章检查"))
    window.sequence_check_btn.setToolTip(
        t("检查章节编号是否连续，发现缺章或编号异常")
    )
    window.sequence_check_btn.setEnabled(False)
    window.split_btn = QtWidgets.QPushButton(t("执行分章"))
    window.split_btn.setToolTip(t("按当前规则执行分章并导出文件"))
    for button in [
        window.preprocess_btn,
        window.analyze_btn,
        window.preview_btn,
        window.sequence_check_btn,
        window.split_btn,
    ]:
        control_row.addWidget(button)
    control_row.addStretch(1)
    window.language_btn = QtWidgets.QToolButton()
    window.language_btn.setPopupMode(
        QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup
    )
    window.language_btn.setToolTip(t("语言"))
    window.language_btn.setIconSize(QtCore.QSize(22, 22))
    window.info_btn = QtWidgets.QToolButton()
    window.info_btn.setToolTip(t("关于"))
    window.info_btn.setIconSize(QtCore.QSize(22, 22))
    window.language_menu = QtWidgets.QMenu(window)
    window.action_lang_auto = window.language_menu.addAction(t("跟随系统"))
    window.action_lang_zh = window.language_menu.addAction("中文")
    window.action_lang_en = window.language_menu.addAction("English")
    window.action_lang_auto.triggered.connect(
        lambda: window.language_changed.emit("auto")
    )
    window.action_lang_zh.triggered.connect(lambda: window.language_changed.emit("zh"))
    window.action_lang_en.triggered.connect(lambda: window.language_changed.emit("en"))
    window.language_btn.setMenu(window.language_menu)
    control_row.addWidget(window.language_btn)
    control_row.addWidget(window.info_btn)
    page_layout.addLayout(control_row)

    split_panel = QtWidgets.QSplitter()
    split_panel.setChildrenCollapsible(False)
    split_panel.setHandleWidth(4)
    page_layout.addWidget(split_panel, 1)

    left_widget = QtWidgets.QWidget()
    left_layout = QtWidgets.QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
    left_splitter.setChildrenCollapsible(False)
    left_splitter.setHandleWidth(1)
    left_layout.addWidget(left_splitter, 1)

    window.regex_group = QtWidgets.QGroupBox(t("切分规则"))
    regex_group_layout = QtWidgets.QVBoxLayout(window.regex_group)
    regex_toolbar = QtWidgets.QHBoxLayout()
    window.add_rule_btn = QtWidgets.QPushButton(t("新增规则"))
    window.clear_rule_btn = QtWidgets.QPushButton(t("清空规则"))
    window.add_preset_btn = QtWidgets.QPushButton()
    window.add_rule_btn.setToolTip(
        t("新增一条正则规则（最多 {count} 条）").format(count=DEFAULT_MAX_REGEX)
    )
    window.clear_rule_btn.setToolTip(t("清空当前所有正则规则"))
    window.add_preset_btn.setToolTip(t("打开预设规则编辑面板"))
    regex_toolbar.addWidget(window.add_rule_btn)
    regex_toolbar.addWidget(window.clear_rule_btn)
    regex_toolbar.addStretch(1)
    regex_toolbar.addWidget(window.add_preset_btn)
    regex_group_layout.addLayout(regex_toolbar)

    regex_scroll = QtWidgets.QScrollArea()
    regex_scroll.setWidgetResizable(True)
    regex_scroll_host = QtWidgets.QWidget()
    window.regex_container = QtWidgets.QVBoxLayout(regex_scroll_host)
    window.regex_container.setContentsMargins(0, 0, 0, 0)
    window.regex_container.setSpacing(8)
    window.regex_container.addStretch(1)
    regex_scroll.setWidget(regex_scroll_host)
    regex_group_layout.addWidget(regex_scroll, 1)
    left_splitter.addWidget(window.regex_group)

    window.config_group = QtWidgets.QGroupBox(t("模板与命名设置"))
    config_layout = QtWidgets.QFormLayout(window.config_group)
    window.edit_template_btn = QtWidgets.QPushButton(t("编辑全局模板"))
    window.edit_template_btn.setToolTip(t("打开模板编辑窗口，设置默认 XHTML 模板"))
    window.h1_name_rule_edit = QtWidgets.QLineEdit()
    window.h2_name_rule_edit = QtWidgets.QLineEdit()
    window.h3_name_rule_edit = QtWidgets.QLineEdit()
    name_rule_tooltip = t(
        "输出文件名的命名规则。可用占位符：\n"
        "  {000}    — 全局序号（3位补零）\n"
        "  {$$$}    — 同级相对序号（3位补零，遇上级重置）\n"
        "  {title}  — 当前标题（特殊字符转下划线）\n"
        "  {h1_no}  — 当前 h1 序号\n"
        "  {h2_no}  — 当前 h2 序号\n"
        "  {h1_no2} — 当前 h1 序号（2位补零）\n"
        "  {h2_no2} — 当前 h2 序号（2位补零）\n"
        "  {h1_no3} — 当前 h1 序号（3位补零）\n"
        "  {h2_no3} — 当前 h2 序号（3位补零）\n"
        "  {h1}     — 最近 h1 标题文本\n"
        "  {h2}     — 最近 h2 标题文本\n"
        "示例：Vol{h1_no3}_Chapter{h2_no3}"
    )
    window.h1_name_rule_edit.setToolTip(name_rule_tooltip)
    window.h2_name_rule_edit.setToolTip(name_rule_tooltip)
    window.h3_name_rule_edit.setToolTip(name_rule_tooltip)
    window.long_title_threshold_spin = QtWidgets.QSpinBox()
    window.long_title_threshold_spin.setRange(20, 500)
    window.long_title_threshold_spin.setValue(DEFAULT_LONG_TITLE_THRESHOLD)
    window.long_title_threshold_spin.setToolTip(t("标题超过该长度时在预览中高亮提示"))
    window.label_template = QtWidgets.QLabel(t("全局模板"))
    window.label_h1 = QtWidgets.QLabel(t("h1 命名规则"))
    window.label_h2 = QtWidgets.QLabel(t("h2 命名规则"))
    window.label_h3 = QtWidgets.QLabel(t("h3 命名规则"))
    window.label_threshold = QtWidgets.QLabel(t("标题高亮阈值"))
    config_layout.addRow(window.label_template, window.edit_template_btn)
    config_layout.addRow(window.label_h1, window.h1_name_rule_edit)
    config_layout.addRow(window.label_h2, window.h2_name_rule_edit)
    config_layout.addRow(window.label_h3, window.h3_name_rule_edit)
    config_layout.addRow(window.label_threshold, window.long_title_threshold_spin)
    left_splitter.addWidget(window.config_group)
    left_splitter.setSizes([360, 160])

    right_widget = QtWidgets.QWidget()
    right_layout = QtWidgets.QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)

    window.preview_group = QtWidgets.QGroupBox(t("预览界面"))
    preview_layout = QtWidgets.QVBoxLayout(window.preview_group)
    preview_toolbar = QtWidgets.QHBoxLayout()
    window.expand_btn = QtWidgets.QPushButton(t("展开全部"))
    window.collapse_btn = QtWidgets.QPushButton(t("折叠全部"))
    window.preview_search_edit = QtWidgets.QLineEdit()
    window.preview_filter_btn = QtWidgets.QPushButton()
    window.preview_filter_btn.setFlat(True)
    window.preview_filter_btn.setText("")
    window.preview_filter_btn.setFixedWidth(34)
    window.preview_filter_btn.clicked.connect(window._open_preview_filter_menu)
    window._build_preview_filter_menu()
    window.preview_search_edit.setPlaceholderText(t("搜索章节标题..."))
    window.preview_search_edit.setMinimumWidth(280)
    window.expand_btn.setToolTip(t("展开预览界面中的所有节点"))
    window.collapse_btn.setToolTip(t("折叠预览界面中的所有节点"))
    window.preview_search_edit.setToolTip(t("按章节标题关键字过滤预览项"))
    window.preview_filter_btn.setToolTip(t("筛选预览项"))
    preview_toolbar.addWidget(window.expand_btn)
    preview_toolbar.addWidget(window.collapse_btn)
    preview_toolbar.addStretch(1)
    preview_toolbar.addWidget(window.preview_search_edit, 1)
    preview_toolbar.addWidget(window.preview_filter_btn, 0)
    preview_layout.addLayout(preview_toolbar)

    window.preview_tree = QtWidgets.QTreeView()
    window.preview_tree.setHeader(
        ProportionalPaddingHeaderView(
            QtCore.Qt.Orientation.Horizontal,
            window.preview_tree,
            left_padding_ratio=0.05,
        )
    )
    window.preview_tree.setStyleSheet(
        "QTreeView::item { min-height: 28px; padding: 2px 0; }"
    )
    window.preview_tree.setAlternatingRowColors(True)
    window.preview_tree.setUniformRowHeights(True)
    window.preview_tree.setSelectionBehavior(
        QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
    )
    window.preview_tree.setEditTriggers(
        QtWidgets.QAbstractItemView.EditTrigger.SelectedClicked
    )
    window.preview_tree.setContextMenuPolicy(
        QtCore.Qt.ContextMenuPolicy.CustomContextMenu
    )
    window.preview_tree.setToolTip(t("右键可复制标题"))
    window.preview_tree.header().setStretchLastSection(False)
    window.preview_tree.header().setSectionResizeMode(
        0, QtWidgets.QHeaderView.ResizeMode.Interactive
    )
    window.preview_tree.header().setSectionResizeMode(
        1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
    )
    window.preview_tree.header().setSectionResizeMode(
        2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
    )
    window.preview_tree.setItemDelegateForColumn(
        1, HeadingLevelDelegate(window.preview_tree)
    )
    window.preview_tree.setItemDelegateForColumn(
        2, CenteredCheckStateDelegate(window.preview_tree)
    )
    window.apply_preview_column_layout()
    preview_layout.addWidget(window.preview_tree, 1)

    right_layout.addWidget(window.preview_group, 1)

    split_panel.addWidget(left_widget)
    split_panel.addWidget(right_widget)
    split_panel.setStretchFactor(0, 1)
    split_panel.setStretchFactor(1, 1)
    split_panel.setSizes([600, 600])
    split_panel.splitterMoved.connect(
        lambda _pos, _index: window.apply_preview_column_layout()
    )

    status_row = QtWidgets.QHBoxLayout()
    window.status_label = QtWidgets.QLabel(t("就绪"))
    window.body_preview_label = QtWidgets.QLabel()
    window.body_preview_label.setTextInteractionFlags(
        QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
    )
    window.body_preview_label.setStyleSheet("QLabel { color: #888; }")
    window.body_preview_label.setText(t("点击章节查看首行内容"))
    status_row.addWidget(window.status_label)
    status_row.addStretch(1)
    status_row.addWidget(window.body_preview_label)
    page_layout.addLayout(status_row)
