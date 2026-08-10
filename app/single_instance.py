"""Egypéldányos futás — több HirlevelKoveto.exe = felesleges CPU."""

from __future__ import annotations

import sys
from typing import Optional

_mutex_handle: Optional[object] = None


def try_acquire_single_instance() -> bool:
    """True, ha ez az első példány. Windows: named mutex."""
    global _mutex_handle
    if sys.platform != "win32":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.CreateMutexW(None, False, "Local\\HirlevelKoveto_SingleInstance_v1")
        err = kernel32.GetLastError()
        _mutex_handle = handle
        # ERROR_ALREADY_EXISTS = 183
        return int(err) != 183
    except Exception:
        return True
