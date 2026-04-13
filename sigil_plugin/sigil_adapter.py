from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Iterable


class SigilAdapterError(RuntimeError):
    """Raised when required Sigil BookContainer APIs are unavailable."""


NAV_ITEMREF_ID = "nav"
LINEAR_NO = "no"


@dataclass
class SigilAdapter:
    """Bridge split output to Sigil edit-plugin runtime."""

    bk: object
    _pending_spine_ids: list[str] = field(default_factory=list)
    _pending_lock: Lock = field(default_factory=Lock)
    _last_exported_name: str = ""

    @staticmethod
    def run_gui(
        config_path: Path,
        sigil_mode: bool = False,
        output_writer: Callable[[str, str], None] | None = None,
        latest_export_name_provider: Callable[[], str] | None = None,
    ) -> int:
        from chapter_splitter.ui.app import run_gui

        return run_gui(
            config_path,
            sigil_mode=sigil_mode,
            output_writer=output_writer,
            latest_export_name_provider=latest_export_name_provider,
        )

    def _require(self, method_name: str) -> Any:
        method = getattr(self.bk, method_name, None)
        if method is None or not callable(method):
            raise SigilAdapterError(f"Sigil BookContainer method is required: {method_name}")
        return method

    def iter_text_items(self) -> Iterable[tuple[str, str]]:
        """Yield `(manifest_id, href)` entries from Sigil text iterator."""
        iterator = self._require("text_iter")
        return iterator()

    def read_text_by_manifest_id(self, manifest_id: str) -> str:
        """Read manifest file content and decode bytes payloads as utf-8 text."""
        readfile = self._require("readfile")
        payload = readfile(manifest_id)
        if isinstance(payload, bytes):
            return payload.decode("utf-8")
        return str(payload)

    def write_text_by_manifest_id(self, manifest_id: str, content: str) -> None:
        """Write updated text content to an existing manifest entry."""
        writefile = self._require("writefile")
        writefile(manifest_id, content)

    def write_xhtml(self, filename: str, content: str) -> str:
        """
        Add a new XHTML file and return its manifest id.

        Sigil expects: addfile(desired_unique_manifest_id, basename, data, mime=...).
        """
        addfile = self._require("addfile")
        addfile(filename, filename, content, "application/xhtml+xml")
        return filename

    def write_xhtml_and_collect(self, filename: str, content: str) -> None:
        file_id = self.write_xhtml(filename, content)
        with self._pending_lock:
            self._pending_spine_ids.append(file_id)
            self._last_exported_name = filename

    def get_last_exported_name(self) -> str:
        with self._pending_lock:
            return self._last_exported_name

    def consume_pending_spine_ids(self) -> list[str]:
        with self._pending_lock:
            collected = list(self._pending_spine_ids)
            self._pending_spine_ids.clear()
            return collected

    def add_xhtml_by_bookpath(self, manifest_id: str, bookpath: str, content: str) -> str:
        """Add an XHTML file using bookpath-aware API when available."""
        addbookpath = self._require("addbookpath")
        return str(addbookpath(manifest_id, bookpath, content, "application/xhtml+xml"))

    def append_to_spine(self, file_ids: list[str]) -> None:
        """
        Append idrefs to spine while supporting both epub3 and legacy APIs.

        - epub3: spine tuples are `(id, linear, properties)`
        - legacy: spine tuples are `(id, linear)`
        """
        if not file_ids:
            return

        getspine_epub3 = getattr(self.bk, "getspine_epub3", None)
        setspine_epub3 = getattr(self.bk, "setspine_epub3", None)
        if callable(getspine_epub3) and callable(setspine_epub3):
            spine = list(getspine_epub3())
            spine.extend((item_id, None, None) for item_id in file_ids)
            spine = [
                (item_id, LINEAR_NO, properties) if item_id == NAV_ITEMREF_ID else (item_id, linear, properties)
                for item_id, linear, properties in spine
            ]
            setspine_epub3(spine)
            return

        getspine = self._require("getspine")
        setspine = self._require("setspine")
        spine = list(getspine())
        spine.extend((item_id, None) for item_id in file_ids)
        spine = [
            (item_id, LINEAR_NO) if item_id == NAV_ITEMREF_ID else (item_id, linear)
            for item_id, linear in spine
        ]
        setspine(spine)
