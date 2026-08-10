from __future__ import annotations

import sys
from pathlib import Path

from app.paths import ROOT


def startup_shortcut_path() -> Path:
    appdata = Path.home() / "AppData" / "Roaming"
    return appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "HirlevelKoveto.lnk"


def _autostart_command() -> tuple[str, str]:
    """(target, arguments)"""
    if getattr(sys, "frozen", False):
        return sys.executable, "--tray"
    return sys.executable, f'"{ROOT / "main.py"}" --tray'


def enable_autostart() -> None:
    """Indításkor minimalizálva induljon (tálca)."""
    target, arguments = _autostart_command()
    try:
        from win32com.client import Dispatch  # type: ignore
    except ImportError:
        bat = startup_shortcut_path().with_suffix(".cmd")
        if getattr(sys, "frozen", False):
            bat.write_text(
                f'@echo off\r\ncd /d "{ROOT}"\r\n"{target}" {arguments}\r\n',
                encoding="utf-8",
            )
        else:
            bat.write_text(
                f'@echo off\r\ncd /d "{ROOT}"\r\n"{target}" {arguments}\r\n',
                encoding="utf-8",
            )
        return

    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(startup_shortcut_path()))
    shortcut.Targetpath = target
    shortcut.Arguments = arguments
    shortcut.WorkingDirectory = str(ROOT)
    shortcut.IconLocation = target
    shortcut.save()


def disable_autostart() -> None:
    for p in (startup_shortcut_path(), startup_shortcut_path().with_suffix(".cmd")):
        if p.exists():
            p.unlink()


def is_autostart_enabled() -> bool:
    return startup_shortcut_path().exists() or startup_shortcut_path().with_suffix(".cmd").exists()
