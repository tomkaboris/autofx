"""Portable AutoFX launcher with an optional Linux Qt/GTK workaround.

Run: python run_desktop.py
To disable the workaround, use: python desktop.py
"""
from __future__ import annotations

import os
import sys

if sys.platform.startswith("linux"):
    # Must be set before importing PySide6 / creating QApplication.
    os.environ.pop("QT_QPA_PLATFORMTHEME", None)
    os.environ.pop("GTK_THEME", None)
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"

from desktop import main

if __name__ == "__main__":
    sys.exit(main())
