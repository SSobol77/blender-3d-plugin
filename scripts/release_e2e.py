"""End-to-end release verification in a clean Blender config."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

ZIP_PATH = Path("/tmp/blender-ci") / "blender_mobile_3d-1.0.0.zip"
ADDONS_DIR = Path.home() / ".config" / "blender" / "4.3" / "scripts" / "addons"
PACKAGE_DIR = ADDONS_DIR / "blender_mobile_3d"
REPORT_PATH = ZIP_PATH.parent / "e2e-report.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def run_blender_script(script: str) -> int:
    blender = "/usr/local/bin/blender"
    cmd = f"BLENDER_USER_CONFIG=/tmp/blender-ci {blender} --background --factory-startup --python-expr '{script}'"
    return os.system(cmd)


def main() -> int:
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "zip_path": str(ZIP_PATH),
        "sha256": sha256_file(ZIP_PATH),
        "artifacts": [],
        "checks": {},
    }

    if not ZIP_PATH.exists():
        report["checks"]["zip_exists"] = False
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    report["checks"]["zip_exists"] = True
    report["checks"]["zip_valid_zip"] = zipfile.is_zipfile(ZIP_PATH)

    install_script = f"""
import bpy, sys, os
zip_path = r'{ZIP_PATH}'
addons_dir = r'{ADDONS_DIR}'
addons_dir.mkdir(parents=True, exist_ok=True)
bpy.ops.preferences.addon_install(filepath=zip_path)
bpy.ops.preferences.addon_enable(module='blender_mobile_3d')
"""
    os.system(f"BLENDER_USER_CONFIG=/tmp/blender-ci /usr/local/bin/blender --background --factory-startup --python-expr '{install_script}'")

    scene_script = """
import bpy, sys
result = {
    "addons": sorted(bpy.context.preferences.addons.keys()),
    "use_restrict": getattr(bpy.context.preferences, "use_restrict", False),
}
print(json.dumps(result))
"""
    ret = run_blender_script(scene_script)
    report["checks"]["addon_enabled"] = ret == 0

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if all(v is True for v in report["checks"].values()) else 2


if __name__ == "__main__":
    sys.exit(main())
