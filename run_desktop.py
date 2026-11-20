"""AutoFX launcher: isolate Linux GUI from VS Code Snap's GTK/GIO environment.

Use: python run_desktop.py
Optional: AUTOFX_QT_PLATFORM=wayland python run_desktop.py
"""
from __future__ import annotations

import os
import sys


def sanitize_linux_gui_environment() -> None:
    if not sys.platform.startswith("linux"):
        return

    # Snap VS Code exports paths from its own runtime into integrated terminals.
    # The resulting mixed GTK/GSettings libraries may abort Qt applications.
    path_vars = (
        "GTK_PATH", "GTK_EXE_PREFIX", "GTK_IM_MODULE_FILE",
        "GSETTINGS_SCHEMA_DIR", "GIO_MODULE_DIR",
        "GDK_PIXBUF_MODULE_FILE", "GDK_PIXBUF_MODULEDIR",
        "LOCPATH", "LD_LIBRARY_PATH", "LD_PRELOAD",
    )
    for key in path_vars:
        value = os.environ.get(key, "")
        if "/snap/code/" in value or "/snap/code" in value:
            original = os.environ.get(key + "_VSCODE_SNAP_ORIG", "")
            if original:
                os.environ[key] = original
            else:
                os.environ.pop(key, None)

    # Restore pre-Snap search paths if VS Code preserved them.
    # Without this, GLib may load schemas from /snap/code/.../usr/share.
    for key in ("XDG_DATA_DIRS", "XDG_CONFIG_DIRS", "XDG_DATA_HOME"):
        value = os.environ.get(key, "")
        if "/snap/code/" in value or "/snap/code" in value:
            original = os.environ.get(key + "_VSCODE_SNAP_ORIG", "")
            if original:
                os.environ[key] = original
            elif key == "XDG_DATA_DIRS":
                os.environ[key] = "/usr/local/share:/usr/share"
            else:
                os.environ.pop(key, None)

    os.environ.pop("QT_QPA_PLATFORMTHEME", None)
    os.environ.pop("GTK_THEME", None)
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
    # Work around some GTK/Wayland integration problems on affected desktops.
    # Can be overridden for native Wayland with AUTOFX_QT_PLATFORM=wayland.
    os.environ["QT_QPA_PLATFORM"] = os.environ.get("AUTOFX_QT_PLATFORM", "xcb")


sanitize_linux_gui_environment()

from desktop import main

if __name__ == "__main__":
    sys.exit(main())
