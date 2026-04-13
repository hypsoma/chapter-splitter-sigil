from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

from PySide6 import QtWidgets

from chapter_splitter.infrastructure.configuration import (
    DEFAULT_UI_LANGUAGE,
    SUPPORTED_UI_LANGUAGES,
    ConfigurationManager,
)
from chapter_splitter.ui.presenter import MainPresenter
from chapter_splitter.ui.i18n import AppTranslator, select_language
from chapter_splitter.ui.view import MainWindow


def run_gui(
    config_path: Path,
    sigil_mode: bool = False,
    output_writer: Callable[[str, str], None] | None = None,
    latest_export_name_provider: Callable[[], str] | None = None,
) -> int:
    if sys.platform.startswith("linux"):
        # Prefer desktop portal integration so file dialogs use system-native pickers.
        os.environ.setdefault("QT_QPA_PLATFORMTHEME", "xdgdesktopportal")

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    config = ConfigurationManager.load(config_path)
    ui_language = str(config.get("ui", {}).get("language", DEFAULT_UI_LANGUAGE)).lower()
    if ui_language not in SUPPORTED_UI_LANGUAGES:
        ui_language = select_language()

    translator = AppTranslator(ui_language)
    app.installTranslator(translator)
    app._app_translator = translator
    view = MainWindow(sigil_mode=sigil_mode)
    _presenter = MainPresenter(
        view,
        config_path,
        output_writer=output_writer,
        sigil_mode=sigil_mode,
        latest_export_name_provider=latest_export_name_provider,
    )
    view.show()
    return app.exec()
