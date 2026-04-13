from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Sigil plugin zip package.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Default: <plugin_name>.zip from plugin.xml",
    )
    return parser.parse_args()


def read_plugin_name(plugin_xml_path: Path) -> str:
    root = ET.fromstring(plugin_xml_path.read_text(encoding="utf-8"))
    plugin_name = (root.findtext("name") or "").strip()
    if not plugin_name:
        raise ValueError("Missing <name> in sigil_plugin/plugin.xml")
    return plugin_name


def should_include(path: Path) -> bool:
    parts = set(path.parts)
    if "__pycache__" in parts:
        return False
    if path.suffix == ".pyc":
        return False
    return True


def write_file(zipf: ZipFile, src: Path, arc: Path) -> None:
    zipf.write(src, arc.as_posix())


def build_package(project_root: Path, output_path: Path | None = None) -> Path:
    plugin_dir = project_root / "sigil_plugin"
    plugin_xml = plugin_dir / "plugin.xml"
    plugin_png = plugin_dir / "plugin.png"
    plugin_py = plugin_dir / "plugin.py"
    config_toml = project_root / "config.toml"
    package_dir = project_root / "chapter_splitter"

    for required in (plugin_xml, plugin_png, plugin_py, config_toml, package_dir):
        if not required.exists():
            raise FileNotFoundError(f"Required path not found: {required}")

    plugin_name = read_plugin_name(plugin_xml)
    zip_path = output_path or (project_root / f"{plugin_name}.zip")

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zipf:
        root = Path(plugin_name)

        write_file(zipf, plugin_xml, root / "plugin.xml")
        write_file(zipf, plugin_png, root / "plugin.png")
        write_file(zipf, plugin_py, root / "plugin.py")
        write_file(zipf, config_toml, root / "config.toml")

        # Include auxiliary plugin-side modules such as sigil_adapter.
        entry_point_names = {"plugin.py", "plugin.xml", "plugin.png"}
        for file_path in sorted(plugin_dir.rglob("*")):
            if not file_path.is_file() or not should_include(file_path):
                continue
            if file_path.name in entry_point_names:
                continue
            rel = file_path.relative_to(project_root)
            write_file(zipf, file_path, root / rel)

        for file_path in sorted(package_dir.rglob("*")):
            if not file_path.is_file() or not should_include(file_path):
                continue
            rel = file_path.relative_to(project_root)
            write_file(zipf, file_path, root / rel)

    return zip_path


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent
    zip_path = build_package(project_root, args.output)
    print(f"Built: {zip_path}")


if __name__ == "__main__":
    main()
