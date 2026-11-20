"""dist_release/HirlevelKoveto-{VERSION_LABEL}-win64.zip a program/ mappából."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROGRAM = ROOT / "program"
OUT = ROOT / "dist_release"


def main() -> None:
    from app.build_info import VERSION_LABEL

    if not (PROGRAM / "HirlevelKoveto.exe").is_file():
        raise SystemExit("Hiányzik: program/HirlevelKoveto.exe — futtasd a BUILD-EXE.cmd-et.")

    OUT.mkdir(exist_ok=True)
    base = OUT / f"HirlevelKoveto-{VERSION_LABEL}-win64"
    zip_path = Path(str(base) + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(base), "zip", PROGRAM)
    print(zip_path)


if __name__ == "__main__":
    main()
