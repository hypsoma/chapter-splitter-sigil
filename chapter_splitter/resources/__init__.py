"""Qt binary resource registration helpers."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore

_RESOURCE_REGISTERED = False


def register_icons_resource() -> None:
    """Register compiled icon resources for `:/icons/*` lookups."""

    global _RESOURCE_REGISTERED
    if _RESOURCE_REGISTERED:
        return

    rcc_path = Path(__file__).with_name("icons.rcc")
    if not rcc_path.exists():
        raise FileNotFoundError(f"Qt resource file not found: {rcc_path}")

    if not QtCore.QResource.registerResource(str(rcc_path)):
        raise RuntimeError(f"Failed to register Qt resource file: {rcc_path}")

    _RESOURCE_REGISTERED = True
