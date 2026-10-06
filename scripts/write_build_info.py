"""BUILD-EXE.cmd: build időbélyeg írása app/build_info.py-ba."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
out = ROOT / "app" / "build_info.py"
stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
out.write_text(f'BUILD_STAMP = "{stamp}"\n', encoding="utf-8")
print(stamp)
