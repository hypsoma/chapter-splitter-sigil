from pathlib import Path
import xml.etree.ElementTree as ET

__all__ = ["__version__"]


def _read_plugin_version() -> str:
    package_dir = Path(__file__).resolve().parent
    candidate_paths = (
        package_dir.parent / "plugin.xml",
        package_dir.parent / "sigil_plugin" / "plugin.xml",
    )

    for plugin_xml_path in candidate_paths:
        try:
            root = ET.fromstring(plugin_xml_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ET.ParseError):
            continue

        version = (root.findtext("version") or "").strip()
        if version:
            return version

    return "unknown"


__version__ = _read_plugin_version()
