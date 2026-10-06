from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Projektgyökér a path-on, ha közvetlenül futtatják
if not getattr(sys, "frozen", False):
    ROOT = Path(__file__).resolve().parent
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Hírlevél követő")
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Indítás tálcára minimalizálva (Windows indításhoz)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Build időbélyeg kiírása és kilépés",
    )
    args = parser.parse_args()

    if args.version:
        try:
            from app.build_info import BUILD_STAMP

            print(f"Hírlevél követő — build: {BUILD_STAMP}")
        except Exception:
            print("Hírlevél követő — build: dev")
        sys.exit(0)

    from app.single_instance import try_acquire_single_instance

    if not try_acquire_single_instance():
        # Második példány = felesleges CPU (tálcán már fut)
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0,
                "A Hírlevél követő már fut a tálcán.\n\n"
                "Új build után: tálca ikon → Kilépés, aztán indítsd újra az exe-t.\n"
                "Egyébként: nyisd meg a tálcáról.",
                "Hírlevél követő",
                0x40,
            )
        except Exception:
            print("A Hírlevél követő már fut.", file=sys.stderr)
        sys.exit(0)

    from app.db import init_db, load_config
    from app.dpi import apply_ctk_scaling, configure_windows_dpi

    scale = configure_windows_dpi()
    apply_ctk_scaling(scale)

    from app.ui import App

    init_db()
    cfg = load_config()
    start_tray = bool(args.tray or cfg.get("start_minimized_to_tray"))

    app = App(start_in_tray=start_tray)
    app.mainloop()


if __name__ == "__main__":
    main()
