"""BUILD-EXE.cmd: build számláló + időbélyeg → app/build_info.py, installer/generated_version.iss."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCT_VERSION = "1.0"
COUNTER_PATH = ROOT / "build_number.txt"
BUILD_INFO = ROOT / "app" / "build_info.py"
INNO_VERSION = ROOT / "installer" / "generated_version.iss"


def _next_build_number() -> int:
    raw = ""
    if COUNTER_PATH.exists():
        raw = COUNTER_PATH.read_text(encoding="utf-8-sig").strip()
    try:
        n = int(raw or "0")
    except ValueError:
        n = 0
    n += 1
    COUNTER_PATH.write_text(f"{n}\n", encoding="utf-8")
    return n


def main() -> None:
    build_no = _next_build_number()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    version_full = f"{PRODUCT_VERSION}.{build_no}"

    BUILD_INFO.write_text(
        f'''"""Auto-generált — ne szerkeszd kézzel (BUILD-EXE.cmd / write_build_info.py)."""

PRODUCT_VERSION = "{PRODUCT_VERSION}"
BUILD_NUMBER = {build_no}
BUILD_STAMP = "{stamp}"
VERSION_LABEL = "{version_full}"
''',
        encoding="utf-8",
    )

    INNO_VERSION.write_text(
        f"; Auto-generált — BUILD-EXE.cmd\n"
        f'#define MyAppVersion "{version_full}"\n'
        f"#define MyAppBuildNumber {build_no}\n",
        encoding="utf-8",
    )

    print(f"build {build_no} ({stamp}) -> {version_full}")


if __name__ == "__main__":
    main()
