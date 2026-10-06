"""Rendszerébredés (alvás / fedél fel) — Windows WM_POWERBROADCAST."""

from __future__ import annotations

import sys
from typing import Any, Callable

WM_POWERBROADCAST = 0x0218
PBT_APMRESUMEAUTOMATIC = 0x12
PBT_APMRESUMESUSPEND = 0x07
GWL_WNDPROC = -4


def bind_system_resume(widget: Any, callback: Callable[[], None]) -> bool:
    """Ébredés után meghívja a callbacket (UI szálon: widget.after)."""
    if sys.platform != "win32":
        return _bind_focus_fallback(widget, callback)
    if getattr(widget, "_resume_bound", False):
        return True
    try:
        from app.win_chrome import hwnd_of

        hwnd = hwnd_of(widget)
        if not hwnd:
            return False

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        LRESULT = ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(
            LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )
        old_wndproc = user32.GetWindowLongPtrW(hwnd, GWL_WNDPROC)
        if not old_wndproc:
            return False

        resume_codes = (PBT_APMRESUMESUSPEND, PBT_APMRESUMEAUTOMATIC)

        def wndproc(h: int, msg: int, wparam: int, lparam: int) -> int:
            try:
                if int(msg) == WM_POWERBROADCAST and int(wparam) in resume_codes:
                    try:
                        widget.after(0, callback)
                    except Exception:
                        pass
            except Exception:
                pass
            return int(
                user32.CallWindowProcW(
                    ctypes.c_void_p(old_wndproc), h, msg, wparam, lparam
                )
            )

        new_proc = WNDPROC(wndproc)
        user32.SetWindowLongPtrW(
            hwnd,
            GWL_WNDPROC,
            ctypes.cast(new_proc, ctypes.c_void_p).value,
        )
        widget._resume_wndproc = new_proc  # type: ignore[attr-defined]
        widget._resume_old_wndproc = old_wndproc  # type: ignore[attr-defined]
        widget._resume_bound = True  # type: ignore[attr-defined]
        return True
    except Exception:
        return False


def _bind_focus_fallback(widget: Any, callback: Callable[[], None]) -> bool:
    if getattr(widget, "_resume_focus_bound", False):
        return True

    def on_activate(_event: object = None) -> None:
        try:
            widget.after(0, callback)
        except Exception:
            pass

    try:
        widget.bind("<Map>", on_activate, add="+")
        widget.bind("<FocusIn>", on_activate, add="+")
        widget._resume_focus_bound = True  # type: ignore[attr-defined]
        return True
    except Exception:
        return False
