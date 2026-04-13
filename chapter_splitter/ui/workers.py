from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from PySide6 import QtCore

from chapter_splitter.application.service import SplitChapterService
from chapter_splitter.domain.document_loader import DocumentLoader


class WorkerSignals(QtCore.QObject):
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)
    progress = QtCore.Signal(int, int)


class LoadTextJob(QtCore.QRunnable):
    def __init__(self, input_path: Path) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._input_path = input_path

    @QtCore.Slot()
    def run(self) -> None:
        try:
            text = DocumentLoader.load_text(self._input_path)
            self.signals.finished.emit(text)
        except Exception as error:  # pragma: no cover
            self.signals.failed.emit(str(error))


class SplitJob(QtCore.QRunnable):
    def __init__(
        self,
        input_path: Path,
        output_dir: Path,
        config: dict[str, Any],
        ignored_indices: set[int],
        write_output: bool = True,
        output_writer: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._service = SplitChapterService()
        self._input_path = input_path
        self._output_dir = output_dir
        self._config = config
        self._ignored_indices = ignored_indices
        self._write_output = write_output
        self._output_writer = output_writer
        self._last_emit = 0.0

    def _emit_progress_throttled(self, done: int, total: int) -> None:
        now = time.monotonic()
        if done == total or (now - self._last_emit) >= 0.1:
            self._last_emit = now
            self.signals.progress.emit(done, total)

    @QtCore.Slot()
    def run(self) -> None:
        try:
            output_dir = self._output_dir if self._write_output else Path("/tmp/chapter_splitter_preview")
            result = self._service.execute(
                self._input_path,
                output_dir,
                self._config,
                self._ignored_indices,
                progress_callback=self._emit_progress_throttled,
                write_output=self._write_output,
                output_writer=self._output_writer,
            )
            self.signals.finished.emit(result)
        except Exception as error:  # pragma: no cover
            self.signals.failed.emit(str(error))
