from __future__ import annotations

from typing import TYPE_CHECKING

from chapter_splitter.infrastructure.configuration import DEFAULT_MAX_REGEX
from chapter_splitter.ui.common import t

if TYPE_CHECKING:
    from chapter_splitter.ui.main_window import MainWindow


def retranslate_main_window(window: MainWindow) -> None:
    window.setWindowTitle(t("分章助手"))
    window.input_path_edit.setPlaceholderText(
        t("请选择待分章的文本文件（支持拖拽 TXT）")
    )
    window.input_path_edit.setToolTip(t("输入或选择要处理的 TXT 文件路径"))
    window.output_dir_edit.setToolTip(t("分章结果输出目录"))
    window.pick_input_btn.setText(t("选择文本"))
    window.pick_input_btn.setToolTip(t("选择待处理的文本文件"))
    window.pick_output_btn.setText(t("选择输出"))
    window.pick_output_btn.setToolTip(t("选择分章结果输出目录"))
    window.preprocess_btn.setText(t("txt预处理"))
    window.preprocess_btn.setToolTip(t("设置文本预处理规则：去除空行、去除段前缩进"))
    window.analyze_btn.setText(t("自动分析"))
    window.analyze_btn.setToolTip(t("根据文本内容自动识别常见章节正则"))
    window.preview_btn.setText(t("预览"))
    window.preview_btn.setToolTip(t("仅生成预览结构，不写入文件"))
    window.sequence_check_btn.setText(t("断章检查"))
    window.sequence_check_btn.setToolTip(
        t("检查章节编号是否连续，发现缺章或编号异常")
    )
    window.split_btn.setText(t("执行分章"))
    window.split_btn.setToolTip(t("按当前规则执行分章并导出文件"))
    window.regex_group.setTitle(t("切分规则"))
    window.add_rule_btn.setText(t("新增规则"))
    window.clear_rule_btn.setText(t("清空规则"))
    window.add_rule_btn.setToolTip(
        t("新增一条正则规则（最多 {count} 条）").format(count=DEFAULT_MAX_REGEX)
    )
    window.clear_rule_btn.setToolTip(t("清空当前所有正则规则"))
    window.add_preset_btn.setText("")
    window.add_preset_btn.setToolTip(t("打开预设规则编辑面板"))
    window.config_group.setTitle(t("模板与命名设置"))
    window.edit_template_btn.setText(t("编辑全局模板"))
    window.edit_template_btn.setToolTip(t("打开模板编辑窗口，设置默认 XHTML 模板"))
    window.label_template.setText(t("全局模板"))
    window.label_h1.setText(t("h1 命名规则"))
    window.label_h2.setText(t("h2 命名规则"))
    window.label_h3.setText(t("h3 命名规则"))
    name_rule_tooltip = t(
        "输出文件名的命名规则。可用占位符：\n"
        "  {000}    — 全局序号（3位补零）\n"
        "  {$$$}    — 同级相对序号（3位补零，遇上级重置）\n"
        "  {title}  — 当前标题（特殊字符转下划线）\n"
        "  {h1_no}  — 当前 h1 序号\n"
        "  {h2_no}  — 当前 h2 序号\n"
        "  {h1_no3} — 当前 h1 序号（3位补零）\n"
        "  {h2_no3} — 当前 h2 序号（3位补零）\n"
        "  {h1}     — 最近 h1 标题文本\n"
        "  {h2}     — 最近 h2 标题文本\n"
        "示例：Vol{h1_no3}_Chapter{h2_no3}"
    )
    window.h1_name_rule_edit.setToolTip(name_rule_tooltip)
    window.h2_name_rule_edit.setToolTip(name_rule_tooltip)
    window.h3_name_rule_edit.setToolTip(name_rule_tooltip)
    window.label_threshold.setText(t("标题高亮阈值"))
    window.preview_group.setTitle(t("预览界面"))
    window.expand_btn.setText(t("展开全部"))
    window.collapse_btn.setText(t("折叠全部"))
    window.expand_btn.setToolTip(t("展开预览界面中的所有节点"))
    window.collapse_btn.setToolTip(t("折叠预览界面中的所有节点"))
    window.preview_search_edit.setPlaceholderText(t("搜索章节标题..."))
    window.preview_search_edit.setToolTip(t("按章节标题关键字过滤预览项"))
    window.preview_filter_btn.setToolTip(t("筛选预览项"))
    window.preview_filter_level_menu.setTitle(t("按级别"))
    for level, action in window.preview_filter_level_actions.items():
        action.setText(level.upper())
    window.preview_filter_include_ignored_action.setText(t("显示已忽略章节"))
    window.preview_filter_problems_only_action.setText(t("仅显示问题章节"))
    window.preview_filter_reset_action.setText(t("重置筛选"))
    window.preview_tree.setToolTip(t("右键可复制标题"))
    window.body_preview_label.setText(t("点击章节查看首行内容"))
    window.action_lang_auto.setText(t("跟随系统"))
    window.action_lang_zh.setText("中文")
    window.action_lang_en.setText("English")
    window.language_btn.setToolTip(t("语言"))
    window.info_btn.setToolTip(t("关于"))
    for row in window._regex_rows:
        row.retranslate_texts()
