#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
import traceback
from pathlib import Path


def _ensure_project_on_path() -> None:
    plugin_dir = Path(__file__).resolve().parent
    project_root = plugin_dir.parent
    root_text = str(project_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


def run(bk: object) -> int:
    """
    Sigil edit-plugin entrypoint.

    Return:
    - 0 on success
    - non-zero on failure
    """
    try:
        _ensure_project_on_path()
        from sigil_plugin.sigil_adapter import SigilAdapter
    except Exception:
        traceback.print_exc()
        return 1

    try:
        adapter = SigilAdapter(bk)
        plugin_dir = Path(__file__).resolve().parent
        candidate_paths = [
            plugin_dir / "config.toml",
            plugin_dir.parent / "config.toml",
        ]
        config_path = next(
            (path for path in candidate_paths if path.exists()),
            candidate_paths[0],
        )

        print("Launching GUI. Please select a local txt file and run Split.")
        adapter.run_gui(
            config_path,
            sigil_mode=True,
            output_writer=adapter.write_xhtml_and_collect,
            latest_export_name_provider=adapter.get_last_exported_name,
        )
        created_ids = adapter.consume_pending_spine_ids()
        adapter.append_to_spine(created_ids)
        print(f"Imported {len(created_ids)} xhtml files into Sigil.")
        return 0
    except Exception:
        traceback.print_exc()
        return 1
