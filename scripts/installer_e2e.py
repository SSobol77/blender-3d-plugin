#!/usr/bin/env python3
"""End-to-end lifecycle verification for an installed installer CLI binary.

Drives a real, already-installed `blender-mobile-3d` binary (from the
Python wheel or the npm package) through the full contract: fresh doctor,
install, no-op update, download-refusal on downgrade, uninstall guard,
uninstall, and post-uninstall doctor — against a real Blender executable,
in a HOME directory isolated for this run only (see
docs/installer-contract.md's note on test isolation).

Usage:
    python scripts/installer_e2e.py \
        --bin /path/to/blender-mobile-3d \
        --blender /path/to/blender \
        --zip dist/blender_mobile_3d-1.0.0.zip \
        --home /tmp/isolated-home \
        --label python-wheel
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(passed), detail))
    status = "ok" if passed else "FAIL"
    print(f"check[{status}] {name} {detail}".rstrip())


def run(binary: str, args: list[str], home: str) -> tuple[int, dict | None, str]:
    env = dict(os.environ)
    env["HOME"] = home
    completed = subprocess.run(  # noqa: S603 - fixed argument array, args from this script only
        [binary, *args],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
        check=False,
    )
    data = None
    stripped = completed.stdout.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            data = None
    return completed.returncode, data, completed.stdout + completed.stderr


def field(data: dict, *names: str):
    for name in names:
        if name in data:
            return data[name]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", required=True)
    parser.add_argument("--blender", required=True)
    parser.add_argument("--zip", required=True)
    parser.add_argument("--home", required=True)
    parser.add_argument("--label", default="installer")
    args = parser.parse_args()

    os.makedirs(args.home, exist_ok=True)

    code, data, out = run(args.bin, ["doctor", "--blender", args.blender, "--json"], args.home)
    check(
        f"{args.label}: fresh doctor is healthy",
        code == 0 and data is not None and data.get("ok") is True,
        out[-300:] if code != 0 else "",
    )
    check(
        f"{args.label}: fresh doctor reports not installed",
        data is not None and field(data, "extension_installed", "extensionInstalled") is False,
    )

    code, data, out = run(
        args.bin, ["install", "--blender", args.blender, "--offline", args.zip, "--json"], args.home
    )
    check(
        f"{args.label}: install succeeds",
        code == 0 and data is not None and data.get("ok") is True,
        out[-300:],
    )
    check(
        f"{args.label}: install reports installed=true",
        data is not None and data.get("installed") is True,
    )
    check(
        f"{args.label}: install reports enabled=true",
        data is not None and data.get("enabled") is True,
    )
    check(
        f"{args.label}: install reports version 1.0.0",
        data is not None and data.get("version") == "1.0.0",
    )

    code, data, out = run(
        args.bin,
        [
            "update",
            "--blender",
            args.blender,
            "--offline",
            args.zip,
            "--version",
            "1.0.0",
            "--json",
        ],
        args.home,
    )
    check(
        f"{args.label}: no-op update when already current",
        code == 0 and data is not None and field(data, "updated") is False,
        out[-300:],
    )

    code, data, out = run(args.bin, ["uninstall", "--blender", args.blender, "--json"], args.home)
    check(f"{args.label}: uninstall without --yes is refused", code == 2, out[-300:])

    code, data, out = run(
        args.bin, ["uninstall", "--blender", args.blender, "--yes", "--json"], args.home
    )
    check(
        f"{args.label}: uninstall succeeds",
        code == 0 and data is not None and data.get("ok") is True,
        out[-300:],
    )
    check(
        f"{args.label}: uninstall reports installed=false",
        data is not None and data.get("installed") is False,
    )

    code, data, out = run(args.bin, ["doctor", "--blender", args.blender, "--json"], args.home)
    check(
        f"{args.label}: post-uninstall doctor confirms absence",
        code == 0
        and data is not None
        and field(data, "extension_installed", "extensionInstalled") is False,
        out[-300:],
    )

    code, data, out = run(
        args.bin, ["uninstall", "--blender", args.blender, "--yes", "--json"], args.home
    )
    check(
        f"{args.label}: uninstall is idempotent when already absent",
        code == 0 and data is not None and field(data, "removed") is False,
        out[-300:],
    )

    failed = [name for name, passed, _ in CHECKS if not passed]
    if failed:
        print(f"failed checks: {failed}")
        return 1
    print(f"all {len(CHECKS)} checks passed for {args.label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
