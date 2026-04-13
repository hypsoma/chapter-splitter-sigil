from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


def t(text: str) -> str:
    return QtCore.QCoreApplication.translate("ui", text)


def themed_icon(
    host: QtWidgets.QWidget,
    resource_name: str,
    size: int,
) -> QtGui.QIcon:
    base_icon = QtGui.QIcon(f":/icons/{resource_name}.svg")
    pixmap = base_icon.pixmap(size, size)
    if pixmap.isNull():
        return base_icon

    def tint(color: QtGui.QColor) -> QtGui.QPixmap:
        image = pixmap.toImage().convertToFormat(
            QtGui.QImage.Format.Format_ARGB32_Premultiplied
        )
        painter = QtGui.QPainter(image)
        painter.setCompositionMode(
            QtGui.QPainter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(image.rect(), color)
        painter.end()
        return QtGui.QPixmap.fromImage(image)

    palette = host.palette()
    icon = QtGui.QIcon()
    icon.addPixmap(
        tint(palette.color(QtGui.QPalette.ColorRole.ButtonText)),
        QtGui.QIcon.Mode.Normal,
        QtGui.QIcon.State.Off,
    )
    icon.addPixmap(
        tint(
            palette.color(
                QtGui.QPalette.ColorGroup.Disabled,
                QtGui.QPalette.ColorRole.ButtonText,
            )
        ),
        QtGui.QIcon.Mode.Disabled,
        QtGui.QIcon.State.Off,
    )
    return icon
