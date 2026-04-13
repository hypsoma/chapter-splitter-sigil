from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

from chapter_splitter.infrastructure.configuration import DEFAULT_LONG_TITLE_THRESHOLD
from chapter_splitter.domain.models import PreviewEntry

SEQUENCE_WARNING_TEXT_COLOR = QtGui.QColor("#CC7722")
LONG_TITLE_TEXT_COLOR = QtGui.QColor("#AD1C42")


@dataclass
class TreeNode:
    entry: PreviewEntry
    parent: "TreeNode | None"
    children: list["TreeNode"]


class PreviewTreeModel(QtCore.QAbstractItemModel):
    HEADERS = ["章节标题", "级别", "忽略"]

    def __init__(self, long_title_threshold: int = DEFAULT_LONG_TITLE_THRESHOLD) -> None:
        super().__init__()
        self._roots: list[TreeNode] = []
        self._flat: list[TreeNode] = []
        self._threshold = long_title_threshold

    def set_entries(self, entries: list[PreviewEntry]) -> None:
        self.beginResetModel()
        self._roots = self._build_tree(entries)
        self._flat = []

        def walk(node: TreeNode) -> None:
            self._flat.append(node)
            for child in node.children:
                walk(child)

        for root in self._roots:
            walk(root)
        self.endResetModel()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        if not parent.isValid():
            return len(self._roots)
        node = parent.internalPointer()
        return len(node.children)

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        _ = parent
        return len(self.HEADERS)

    def index(
        self, row: int, column: int, parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> QtCore.QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            node = self._roots[row]
            return self.createIndex(row, column, node)

        parent_node = parent.internalPointer()
        node = parent_node.children[row]
        return self.createIndex(row, column, node)

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        if not index.isValid():
            return QtCore.QModelIndex()
        node = index.internalPointer()
        parent_node = node.parent
        if parent_node is None:
            return QtCore.QModelIndex()

        grand = parent_node.parent
        siblings = self._roots if grand is None else grand.children
        parent_row = siblings.index(parent_node)
        return self.createIndex(parent_row, 0, parent_node)

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int = QtCore.Qt.DisplayRole,
    ):
        if orientation == QtCore.Qt.Horizontal and 0 <= section < len(self.HEADERS):
            if role == QtCore.Qt.DisplayRole:
                return QtCore.QCoreApplication.translate("ui", self.HEADERS[section])
            if role == QtCore.Qt.ToolTipRole:
                tips = [
                    QtCore.QCoreApplication.translate(
                        "ui", "章节标题列：显示章节名称；双击可编辑"
                    ),
                    QtCore.QCoreApplication.translate(
                        "ui", "级别列：点击可下拉选择 h1-h6"
                    ),
                    QtCore.QCoreApplication.translate(
                        "ui", "忽略列：勾选后该章节不会导出"
                    ),
                ]
                return tips[section]
            return None
        if role != QtCore.Qt.DisplayRole:
            return None
        return str(section + 1)

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        node: TreeNode = index.internalPointer()
        entry = node.entry
        column = index.column()

        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return entry.title
            if column == 1:
                return entry.level
            if column == 2:
                return ""
        if role == QtCore.Qt.ToolTipRole:
            if column == 0:
                if entry.sequence_warning:
                    return entry.sequence_warning
                if len(entry.title) > self._threshold:
                    template = QtCore.QCoreApplication.translate(
                        "ui", "标题过长：{length} 字（阈值 {threshold}）"
                    )
                    return template.format(
                        length=len(entry.title), threshold=self._threshold
                    )
                return QtCore.QCoreApplication.translate("ui", "双击编辑章节标题")
            if column == 1:
                return QtCore.QCoreApplication.translate(
                    "ui", "点击选择标题级别（h1-h6）"
                )
            if column == 2:
                return QtCore.QCoreApplication.translate(
                    "ui", "勾选后忽略该章节，不参与导出"
                )

        if role == QtCore.Qt.CheckStateRole and column == 2:
            return (
                QtCore.Qt.CheckState.Checked
                if entry.ignored
                else QtCore.Qt.CheckState.Unchecked
            )

        if role == QtCore.Qt.ForegroundRole:
            if entry.ignored:
                palette = QtWidgets.QApplication.palette()
                return QtGui.QBrush(
                    palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
                )
            if entry.sequence_warning:
                return QtGui.QBrush(SEQUENCE_WARNING_TEXT_COLOR)
            if len(entry.title) > self._threshold:
                return QtGui.QBrush(LONG_TITLE_TEXT_COLOR)

        if role == QtCore.Qt.FontRole:
            font = QtGui.QFont()
            if entry.ignored:
                font.setStrikeOut(True)
            if entry.level == "h1":
                font.setBold(True)
            return font
        return None

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        flags = QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        if index.column() == 1:
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        if index.column() == 2:
            flags |= QtCore.Qt.ItemFlag.ItemIsUserCheckable
        return flags

    def setData(
        self, index: QtCore.QModelIndex, value, role: int = QtCore.Qt.EditRole
    ) -> bool:
        if not index.isValid():
            return False
        node: TreeNode = index.internalPointer()
        entry = node.entry

        if role == QtCore.Qt.CheckStateRole and index.column() == 2:
            numeric_value = value.value if hasattr(value, "value") else value
            is_checked = numeric_value == QtCore.Qt.CheckState.Checked.value
            entry.ignored = is_checked
            row_start = self.index(index.row(), 0, index.parent())
            row_end = self.index(index.row(), self.columnCount() - 1, index.parent())
            self.dataChanged.emit(
                row_start,
                row_end,
                [
                    QtCore.Qt.CheckStateRole,
                    QtCore.Qt.DisplayRole,
                    QtCore.Qt.FontRole,
                    QtCore.Qt.ForegroundRole,
                ],
            )
            return True

        if role == QtCore.Qt.EditRole and index.column() == 0:
            text = str(value).strip()
            if not text:
                return False
            entry.title = text
            self.dataChanged.emit(
                index,
                index,
                [
                    QtCore.Qt.DisplayRole,
                    QtCore.Qt.ForegroundRole,
                    QtCore.Qt.ToolTipRole,
                ],
            )
            return True
        if role == QtCore.Qt.EditRole and index.column() == 1:
            level = str(value).strip().lower()
            if level not in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                return False
            entry.level = level
            self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])
            return True
        return False

    def toggle_ignored(self, model_index: QtCore.QModelIndex) -> None:
        if not model_index.isValid():
            return
        node = model_index.internalPointer()
        state = (
            QtCore.Qt.CheckState.Unchecked
            if node.entry.ignored
            else QtCore.Qt.CheckState.Checked
        )
        check_index = self.index(model_index.row(), 2, model_index.parent())
        self.setData(check_index, state, QtCore.Qt.CheckStateRole)

    def ignored_indices(self) -> set[int]:
        return {node.entry.index for node in self._flat if node.entry.ignored}

    def title_from_index(self, model_index: QtCore.QModelIndex) -> str:
        if not model_index.isValid():
            return ""
        return model_index.internalPointer().entry.title

    def set_title(self, model_index: QtCore.QModelIndex, new_title: str) -> bool:
        title_index = self.index(model_index.row(), 0, model_index.parent())
        return self.setData(title_index, new_title, QtCore.Qt.EditRole)

    def set_long_title_threshold(self, threshold: int) -> None:
        self._threshold = threshold
        self.layoutChanged.emit()

    def is_problem_entry(self, entry: PreviewEntry) -> bool:
        return bool(entry.sequence_warning) or len(entry.title) > self._threshold

    @staticmethod
    def _build_tree(entries: list[PreviewEntry]) -> list[TreeNode]:
        roots: list[TreeNode] = []
        latest_by_level: dict[int, TreeNode] = {}

        def level_number(level_name: str) -> int:
            try:
                return int(level_name[1:])
            except ValueError:
                return 6

        for entry in entries:
            current_level = level_number(entry.level)
            parent: TreeNode | None = None
            for candidate_level in range(current_level - 1, 0, -1):
                parent = latest_by_level.get(candidate_level)
                if parent is not None:
                    break

            node = TreeNode(entry=entry, parent=parent, children=[])
            latest_by_level[current_level] = node
            for deeper in range(current_level + 1, 7):
                latest_by_level.pop(deeper, None)

            if parent is None:
                roots.append(node)
            else:
                parent.children.append(node)

        return roots


class PreviewFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self.setRecursiveFilteringEnabled(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterKeyColumn(0)
        self._visible_levels: set[str] = {"h1", "h2", "h3", "h4", "h5", "h6"}
        self._show_ignored = True
        self._problems_only = False

    def set_visible_levels(self, levels: set[str]) -> None:
        normalized = {str(level).strip().lower() for level in levels}
        self._visible_levels = {
            level
            for level in normalized
            if level in {"h1", "h2", "h3", "h4", "h5", "h6"}
        } or {"h1", "h2", "h3", "h4", "h5", "h6"}
        self.invalidateFilter()

    def set_show_ignored(self, show_ignored: bool) -> None:
        self._show_ignored = bool(show_ignored)
        self.invalidateFilter()

    def set_problems_only(self, problems_only: bool) -> None:
        self._problems_only = bool(problems_only)
        self.invalidateFilter()

    def set_title_keyword(self, keyword: str) -> None:
        self.setFilterFixedString(keyword.strip())
        self.invalidateFilter()

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QtCore.QModelIndex,
    ) -> bool:
        source_model = self.sourceModel()
        if source_model is None:
            return True

        source_index = source_model.index(source_row, 0, source_parent)
        if not source_index.isValid():
            return False

        node = source_index.internalPointer()
        entry = node.entry

        if entry.level not in self._visible_levels:
            return False
        if not self._show_ignored and entry.ignored:
            return False
        if self._problems_only:
            if isinstance(source_model, PreviewTreeModel):
                if not source_model.is_problem_entry(entry):
                    return False
            elif not bool(entry.sequence_warning):
                return False

        text = str(
            source_model.data(source_index, QtCore.Qt.ItemDataRole.DisplayRole) or ""
        )
        pattern = self.filterRegularExpression()
        if pattern.pattern() and not pattern.match(text).hasMatch():
            return False
        return True
