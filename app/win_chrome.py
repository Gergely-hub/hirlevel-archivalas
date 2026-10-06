"""Keret nélküli ablak Win32-vel — címsor nélkül, tálca látszik (work area)."""

from __future__ import annotations

import sys
from typing import Any, Optional

GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_MAXIMIZEBOX = 0x00010000
WS_MINIMIZEBOX = 0x00020000
WS_SYSMENU = 0x00080000
WS_EX_APPWINDOW = 0x00040000
WS_EX_TOOLWINDOW = 0x00000080
SW_MINIMIZE = 6
SW_RESTORE = 9
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
MONITOR_DEFAULTTONEAREST = 2
MONITOR_DEFAULTTOPRIMARY = 1
SPI_GETWORKAREA = 48


def primary_work_area() -> tuple[int, int, int, int]:
    """Elsődleges monitor munkaterülete — ablak létrehozása ELŐTT is (nincs fix 1280×760)."""
    if sys.platform == "win32":
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            user32 = ctypes.windll.user32
            rc = RECT()
            if user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rc), 0):
                return (
                    int(rc.left),
                    int(rc.top),
                    max(400, int(rc.right - rc.left)),
                    max(300, int(rc.bottom - rc.top)),
                )
        except Exception:
            pass
    return (0, 0, 1040, 620)


def hwnd_of(widget: Any) -> int:
    if sys.platform != "win32":
        return 0
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = int(widget.winfo_id())
        for _ in range(5):
            parent = int(user32.GetParent(hwnd) or 0)
            if not parent:
                break
            hwnd = parent
        return int(hwnd)
    except Exception:
        return 0


def strip_title_bar(widget: Any) -> None:
    """Címsor le — nem overrideredirect (DPI-nél levágna)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = hwnd_of(widget)
        if not hwnd:
            return
        style = int(user32.GetWindowLongW(hwnd, GWL_STYLE))
        style &= ~(WS_CAPTION | WS_THICKFRAME)
        style |= WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        ex = int(user32.GetWindowLongW(hwnd, GWL_EXSTYLE))
        ex = (ex & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
        )
    except Exception:
        pass


def _work_area(hwnd: int) -> Optional[tuple[int, int, int, int]]:
    """Monitor munkaterület: left, top, width, height — tálca NÉLKÜL."""
    try:
        import ctypes
        from ctypes import wintypes

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        user32 = ctypes.windll.user32
        monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        if not monitor:
            return None
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(monitor, ctypes.byref(mi)):
            return None
        r = mi.rcWork
        return (
            int(r.left),
            int(r.top),
            max(400, int(r.right - r.left)),
            max(300, int(r.bottom - r.top)),
        )
    except Exception:
        return None


def _window_rect(hwnd: int) -> Optional[tuple[int, int, int, int]]:
    try:
        import ctypes
        from ctypes import wintypes

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        rc = RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rc)):
            return None
        return (
            int(rc.left),
            int(rc.top),
            max(200, int(rc.right - rc.left)),
            max(150, int(rc.bottom - rc.top)),
        )
    except Exception:
        return None


def maximize(widget: Any) -> None:
    """Munkaterületre (tálca látszik). Nem SW_MAXIMIZE — az keret nélkül eltakarja a tálcát."""
    if sys.platform != "win32":
        try:
            widget.state("zoomed")
        except Exception:
            pass
        return
    try:
        import ctypes

        hwnd = hwnd_of(widget)
        if not hwnd:
            return
        if not getattr(widget, "_chrome_maximized", False):
            setattr(widget, "_chrome_restore", _window_rect(hwnd))
        area = _work_area(hwnd)
        if not area:
            return
        x, y, w, h = area
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, x, y, w, h, SWP_NOZORDER | SWP_SHOWWINDOW | SWP_FRAMECHANGED
        )
        setattr(widget, "_chrome_maximized", True)
        try:
            widget._win_maximized = True
        except Exception:
            pass
    except Exception:
        pass


def minimize(widget: Any) -> None:
    if sys.platform != "win32":
        try:
            widget.iconify()
        except Exception:
            pass
        return
    try:
        import ctypes

        hwnd = hwnd_of(widget)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
            return
    except Exception:
        pass
    try:
        widget.iconify()
    except Exception:
        pass


def restore(widget: Any) -> None:
    if sys.platform != "win32":
        try:
            widget.state("normal")
        except Exception:
            pass
        return
    try:
        import ctypes

        hwnd = hwnd_of(widget)
        if not hwnd:
            return
        rect = getattr(widget, "_chrome_restore", None)
        setattr(widget, "_chrome_maximized", False)
        try:
            widget._win_maximized = False
        except Exception:
            pass
        if rect:
            x, y, w, h = rect
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, x, y, w, h, SWP_NOZORDER | SWP_SHOWWINDOW | SWP_FRAMECHANGED
            )
        else:
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
    except Exception:
        pass


def is_maximized(widget: Any) -> bool:
    if getattr(widget, "_chrome_maximized", False):
        return True
    if sys.platform != "win32":
        try:
            return str(widget.state()) == "zoomed"
        except Exception:
            return False
    return False


def toggle_maximize(widget: Any) -> None:
    if is_maximized(widget):
        restore(widget)
    else:
        maximize(widget)
