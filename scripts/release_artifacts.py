#!/usr/bin/env python3
"""Build v1.0.0 release artifacts."""
from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path("/home/astra/blender-3d-plugin")
ADDON_DIR = ROOT / "blender_mobile_3d"
BUILD_DIR = ROOT / "dist"
VERSION = "1.0.0"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_addon_zip() -> Path:
    BUILD_DIR.mkdir(exist_ok=True)
    addon_name = f"blender_mobile_3d-{VERSION}.zip"
    zip_path = BUILD_DIR / addon_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ADDON_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(ROOT))
    return zip_path


def main() -> int:
    zip_path = build_addon_zip()
    checksum = sha256_file(zip_path)
    checksum_path = BUILD_DIR / f"blender_mobile_3d-{VERSION}.zip.sha256"
    checksum_path.write_text(f"{checksum}  {zip_path.name}\n", encoding="utf-8")
    print(f"addon_zip={zip_path}")
    print(f"sha256={checksum}")
    print(f"checksum_file={checksum_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
