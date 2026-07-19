#!/usr/bin/env python3
"""End-to-end release verification: build artifacts, then run the Blender
regression suite against the built ZIP in an isolated Blender user profile.

Usage:
    python scripts/release_e2e.py [--blender /path/to/blender] [--workdir DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGRESSION_SCRIPT = REPO_ROOT / "scripts" / "blender_regression.py"
BLENDER_TIMEOUT_SECONDS = 600


def build_artifacts() -> Path:
    from release_artifacts import build_release

    artifacts = build_release(REPO_ROOT)
    return artifacts["zip"]


def run_blender_regression(blender: str, zip_path: Path, workdir: Path) -> int:
    blender_path = shutil.which(blender) or blender
    if not Path(blender_path).is_file():
        print(f"release_e2e: blender executable not found: {blender}", file=sys.stderr)
        return 1

    user_dir = workdir / "blender-user"
    output_dir = workdir / "regression-output"
    user_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["BLENDER_USER_RESOURCES"] = str(user_dir)

    cmd = [
        blender_path,
        "--background",
        "--factory-startup",
        "--python",
        str(REGRESSION_SCRIPT),
        "--",
        "--zip",
        str(zip_path),
        "--output",
        str(output_dir),
    ]
    # The command is a fixed argument array (no shell); the only variable
    # element is the operator-chosen Blender executable path.
    completed = subprocess.run(  # noqa: S603
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=BLENDER_TIMEOUT_SECONDS,
        check=False,
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)

    passed = completed.returncode == 0 and "REGRESSION_RESULT: PASS" in completed.stdout
    report = {
        "zip": str(zip_path),
        "returncode": completed.returncode,
        "passed": passed,
    }
    (workdir / "e2e-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="release_e2e")
    parser.add_argument("--blender", default="blender", help="Blender executable")
    parser.add_argument("--workdir", default=None, help="Working directory (default: temp)")
    args = parser.parse_args()

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        zip_path = build_artifacts()
    except Exception as exc:
        print(f"release_e2e: artifact build failed: {exc}", file=sys.stderr)
        return 1

    if args.workdir:
        workdir = Path(args.workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        return run_blender_regression(args.blender, zip_path, workdir)
    with tempfile.TemporaryDirectory(prefix="bm3d-e2e-") as tmp:
        return run_blender_regression(args.blender, zip_path, Path(tmp))


if __name__ == "__main__":
    sys.exit(main())
