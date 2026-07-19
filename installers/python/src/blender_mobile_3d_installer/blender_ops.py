"""Invoke blender_helper.py inside Blender via an explicit argument array."""

from __future__ import annotations

import json
import subprocess
import tempfile
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from blender_mobile_3d_installer.exit_codes import INSTALL_FAILURE, InstallerError

BLENDER_OP_TIMEOUT_SECONDS = 120
MODULE_NAME = "blender_mobile_3d"


def _helper_script_path() -> Traversable:
    return resources.files("blender_mobile_3d_installer.data") / "blender_helper.py"


def _run_helper(blender_path: str, request: dict) -> dict:
    helper = _helper_script_path()
    cmd = [
        blender_path,
        "--background",
        "--factory-startup",
        "--python",
        str(helper),
        "--",
        json.dumps(request),
    ]
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argument array, no shell
            cmd,
            capture_output=True,
            text=True,
            timeout=BLENDER_OP_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstallerError(INSTALL_FAILURE, f"Failed to run Blender helper: {exc}") from exc

    if completed.returncode != 0:
        raise InstallerError(
            INSTALL_FAILURE,
            f"Blender exited with code {completed.returncode}.\n{completed.stderr[-2000:]}",
        )

    json_line = None
    for line in reversed(completed.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            json_line = line
            break
    if json_line is None:
        raise InstallerError(
            INSTALL_FAILURE, f"Blender helper produced no JSON result.\n{completed.stdout[-2000:]}"
        )

    try:
        result = json.loads(json_line)
    except json.JSONDecodeError as exc:
        raise InstallerError(
            INSTALL_FAILURE, f"Blender helper produced invalid JSON: {exc}"
        ) from exc

    if not result.get("ok", False):
        raise InstallerError(
            INSTALL_FAILURE, f"Blender helper reported failure: {result.get('error')}"
        )
    return result


def status(blender_path: str, module_name: str = MODULE_NAME) -> dict:
    return _run_helper(blender_path, {"action": "status", "module": module_name})


def install(
    blender_path: str, zip_path: Path, overwrite: bool = True, module_name: str = MODULE_NAME
) -> dict:
    return _run_helper(
        blender_path,
        {
            "action": "install",
            "module": module_name,
            "zip_path": str(zip_path),
            "overwrite": overwrite,
        },
    )


def uninstall(blender_path: str, module_name: str = MODULE_NAME) -> dict:
    return _run_helper(blender_path, {"action": "uninstall", "module": module_name})


def make_temp_dir(prefix: str = "bm3d-installer-") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))
