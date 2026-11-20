"""Start AutoFX without inheriting VS Code Snap GTK/GSettings configuration.

Usage: python run_desktop.py
"""
from __future__ import annotations

import os
import sys

if sys.platform.startswith("linux"):
    # VS Code installed via Snap may export GTK_PATH and GSETTINGS_SCHEMA_DIR
    # into its integrated terminal. Those paths can point Qt/GTK to mismatched
    # schemas and crash startup before QApplication is created.
    for key in ("GTK_PATH", "GSETTINGS_SCHEMA_DIR"):
        value = os.environ.get(key, "")
        if "/snap/code/" in value or "/snap/code" in value:
            os.environ.pop(key, None)

    # Run with Qt's platform-neutral styling rather than a GTK theme plugin.
    os.environ.pop("QT_QPA_PLATFORMTHEME", None)
    os.environ.pop("GTK_THEME", None)
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"

from desktop import main

if __name__ == "__main__":
    sys.exit(main())
