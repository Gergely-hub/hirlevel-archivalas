from __future__ import annotations

"""Ikon .ico generálása a buildhez / repohoz."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.app_icon import write_ico  # noqa: E402


def main() -> None:
    dest = ROOT / "app" / "assets" / "hirlevel.ico"
    write_ico(dest)
    print(dest)


if __name__ == "__main__":
    main()
