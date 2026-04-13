from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets

from chapter_splitter.ui.common import t, themed_icon


class HeadingLevelDelegate(QtWidgets.QStyledItemDelegate):
    LEVELS = ["h1", "h2", "h3", "h4", "h5", "h6"]

    def createEditor(self, parent, option, index):
        if index.column() != 1:
            return super().createEditor(parent, option, index)
        editor = QtWidgets.QComboBox(parent)
        editor.addItems(self.LEVELS)
        return editor

    def setEditorData(self, editor, index):
        if isinstance(editor, QtWidgets.QComboBox):
            current = str(index.data(QtCore.Qt.ItemDataRole.DisplayRole) or "h2")
            editor.setCurrentText(current if current in self.LEVELS else "h2")
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtWidgets.QComboBox):
            model.setData(index, editor.currentText(), QtCore.Qt.ItemDataRole.EditRole)
            return
        super().setModelData(editor, model, index)


class CenteredCheckStateDelegate(QtWidgets.QStyledItemDelegate):
    def paint(
        self,
        painter: QtWidgets.QStylePainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> None:
        check_state = index.data(QtCore.Qt.ItemDataRole.CheckStateRole)
        if check_state is None:
            super().paint(painter, option, index)
            return

        style_option = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(style_option, index)
        style_option.features &= ~QtWidgets.QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        style_option.text = ""
        style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
        style.drawControl(
            QtWidgets.QStyle.ControlElement.CE_ItemViewItem,
            style_option,
            painter,
            option.widget,
        )

        indicator_option = QtWidgets.QStyleOptionViewItem(style_option)
        indicator_option.rect = self._centered_indicator_rect(indicator_option, option.widget)
        indicator_option.state &= ~(
            QtWidgets.QStyle.StateFlag.State_On
            | QtWidgets.QStyle.StateFlag.State_Off
            | QtWidgets.QStyle.StateFlag.State_NoChange
        )
        if check_state == QtCore.Qt.CheckState.Checked:
            indicator_option.state |= QtWidgets.QStyle.StateFlag.State_On
        elif check_state == QtCore.Qt.CheckState.PartiallyChecked:
            indicator_option.state |= QtWidgets.QStyle.StateFlag.State_NoChange
        else:
            indicator_option.state |= QtWidgets.QStyle.StateFlag.State_Off

        style.drawPrimitive(
            QtWidgets.QStyle.PrimitiveElement.PE_IndicatorItemViewItemCheck,
            indicator_option,
            painter,
            option.widget,
        )

    def editorEvent(
        self,
        event: QtCore.QEvent,
        model: QtCore.QAbstractItemModel,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> bool:
        if not (index.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable):
            return False
        if not (index.flags() & QtCore.Qt.ItemFlag.ItemIsEnabled):
            return False

        event_type = event.type()
        if event_type in {
            QtCore.QEvent.Type.MouseButtonPress,
            QtCore.QEvent.Type.MouseMove,
            QtCore.QEvent.Type.MouseButtonDblClick,
        }:
            return True
        if event_type == QtCore.QEvent.Type.MouseButtonRelease:
            if not isinstance(event, QtGui.QMouseEvent):
                return False
            if not self._centered_indicator_rect(option, option.widget).contains(
                event.position().toPoint()
            ):
                return False
        elif event_type == QtCore.QEvent.Type.KeyPress:
            if not isinstance(event, QtGui.QKeyEvent):
                return False
            if event.key() not in (QtCore.Qt.Key.Key_Space, QtCore.Qt.Key.Key_Select):
                return False
        else:
            return False

        current_value = index.data(QtCore.Qt.ItemDataRole.CheckStateRole)
        next_state = (
            QtCore.Qt.CheckState.Unchecked
            if current_value == QtCore.Qt.CheckState.Checked
            else QtCore.Qt.CheckState.Checked
        )
        return model.setData(index, next_state, QtCore.Qt.ItemDataRole.CheckStateRole)

    def _centered_indicator_rect(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        widget: QtWidgets.QWidget | None,
    ) -> QtCore.QRect:
        style = widget.style() if widget else QtWidgets.QApplication.style()
        indicator_width = style.pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_IndicatorWidth,
            option,
            widget,
        )
        indicator_height = style.pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_IndicatorHeight,
            option,
            widget,
        )
        if indicator_width <= 0:
            indicator_width = 16
        else:
            indicator_width = max(1, int(round(indicator_width * 1.2)))
        if indicator_height <= 0:
            indicator_height = 16
        else:
            indicator_height = max(1, int(round(indicator_height * 1.2)))
        centered_left = option.rect.x() + (option.rect.width() - indicator_width) // 2
        centered_top = option.rect.y() + (option.rect.height() - indicator_height) // 2
        return QtCore.QRect(
            centered_left,
            centered_top,
            indicator_width,
            indicator_height,
        )


class ProportionalPaddingHeaderView(QtWidgets.QHeaderView):
    def __init__(
        self,
        orientation: QtCore.Qt.Orientation,
        parent: QtWidgets.QWidget | None = None,
        left_padding_ratio: float = 0.1,
    ) -> None:
        super().__init__(orientation, parent)
        self._left_padding_ratio = max(0.0, float(left_padding_ratio))

    def paintSection(
        self, painter: QtGui.QPainter, rect: QtCore.QRect, logical_index: int
    ) -> None:
        if not rect.isValid():
            return

        option = QtWidgets.QStyleOptionHeader()
        self.initStyleOption(option)
        self.initStyleOptionForIndex(option, logical_index)
        option.rect = rect

        style = self.style()
        style.drawControl(
            QtWidgets.QStyle.ControlElement.CE_HeaderSection,
            option,
            painter,
            self,
        )

        header_text = self.model().headerData(
            logical_index,
            self.orientation(),
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        if header_text is None:
            return

        text_rect = style.subElementRect(
            QtWidgets.QStyle.SubElement.SE_HeaderLabel,
            option,
            self,
        )
        text_rect.adjust(int(rect.width() * self._left_padding_ratio), 0, 0, 0)
        style.drawItemText(
            painter,
            text_rect,
            QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft,
            option.palette,
            True,
            str(header_text),
            QtGui.QPalette.ColorRole.ButtonText,
        )


class RegexRow(QtWidgets.QWidget):
    remove_clicked = QtCore.Signal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText(t("规则名称"))
        self.name_edit.setToolTip(t("用于识别这条规则的名称，不参与正则匹配"))
        self.pattern_combo = QtWidgets.QComboBox()
        self.pattern_combo.setEditable(True)
        self.pattern_combo.setMinimumWidth(260)
        self.pattern_combo.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.pattern_combo.lineEdit().setPlaceholderText(
            t("正则表达式（可下拉选择预置）")
        )
        self.pattern_combo.setToolTip(t("可直接输入正则，也可在下拉列表选择预置模式"))
        self.level_combo = QtWidgets.QComboBox()
        self.level_combo.addItems(["h1", "h2", "h3", "h4", "h5", "h6"])
        self.level_combo.setMinimumWidth(56)
        self.level_combo.setToolTip(t("匹配成功后应用的标题级别"))
        self.split_check = QtWidgets.QCheckBox()
        self.split_check.setToolTip(t("勾选后命中该规则时会创建新章节文件"))
        self.split_check.setChecked(True)
        self.remove_btn = QtWidgets.QToolButton()
        self.remove_btn.setFixedWidth(28)
        self.remove_btn.setToolTip(t("删除规则"))
        self._apply_icon()
        self.remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self))
        self.pattern_combo.currentIndexChanged.connect(self._apply_selected_preset)

        layout.addWidget(self.name_edit, 3)
        layout.addWidget(self.pattern_combo, 16)
        layout.addWidget(self.level_combo, 0)
        layout.addWidget(self.split_check, 0)
        layout.addWidget(self.remove_btn, 0)

    def set_preset_options(self, presets: list[dict[str, str]]) -> None:
        self.pattern_combo.blockSignals(True)
        self.pattern_combo.clear()
        for preset in presets:
            self.pattern_combo.addItem(preset["pattern"], preset)
        self.pattern_combo.blockSignals(False)

    def pattern_text(self) -> str:
        return self.pattern_combo.currentText().strip()

    def set_pattern_text(self, pattern: str) -> None:
        self.pattern_combo.setCurrentText(pattern)

    def _apply_selected_preset(self) -> None:
        payload = self.pattern_combo.currentData()
        if not isinstance(payload, dict):
            return
        self.name_edit.setText(payload.get("name", self.name_edit.text()))
        self.level_combo.setCurrentText(
            payload.get("level", self.level_combo.currentText())
        )
        self.split_check.setChecked(True)

    def retranslate_texts(self) -> None:
        self.name_edit.setPlaceholderText(t("规则名称"))
        self.name_edit.setToolTip(t("用于识别这条规则的名称，不参与正则匹配"))
        self.pattern_combo.lineEdit().setPlaceholderText(
            t("正则表达式（可下拉选择预置）")
        )
        self.pattern_combo.setToolTip(t("可直接输入正则，也可在下拉列表选择预置模式"))
        self.level_combo.setToolTip(t("匹配成功后应用的标题级别"))
        self.split_check.setToolTip(t("勾选后命中该规则时会创建新章节文件"))
        self.remove_btn.setToolTip(t("删除规则"))

    def _apply_icon(self) -> None:
        self.remove_btn.setIcon(themed_icon(self, "trash-alt", 16))

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() in {
            QtCore.QEvent.Type.PaletteChange,
            QtCore.QEvent.Type.ApplicationPaletteChange,
        }:
            self._apply_icon()
