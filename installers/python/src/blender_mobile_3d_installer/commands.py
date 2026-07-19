"""CLI entrypoint dispatching to blender_mobile_3d_installer.installer."""

from __future__ import annotations

import argparse
import json
import sys

from blender_mobile_3d_installer import installer
from blender_mobile_3d_installer.exit_codes import (
    BLENDER_NOT_FOUND,
    INVALID_ARGUMENTS,
    PERMISSION_FAILURE,
    SUCCESS,
    InstallerError,
)

INSTALLER_VERSION = "1.0.0"
DEFAULT_ADDON_VERSION = "1.0.0"


class _ArgumentParser(argparse.ArgumentParser):
    """Raises InstallerError instead of calling sys.exit on bad arguments."""

    def error(self, message: str) -> None:  # type: ignore[override]
        raise InstallerError(INVALID_ARGUMENTS, message)


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="blender-mobile-3d")
    sub = parser.add_subparsers(dest="command", parser_class=_ArgumentParser)

    def add_common(p: argparse.ArgumentParser, *, artifact: bool = False) -> None:
        p.add_argument("--blender", default=None, help="Explicit Blender executable path")
        p.add_argument("--json", action="store_true", help="Machine-readable output")
        if artifact:
            p.add_argument("--version", default=DEFAULT_ADDON_VERSION, dest="addon_version")
            p.add_argument("--offline", default=None, dest="offline_zip", metavar="ZIP_PATH")
            p.add_argument("--manifest-url", default=None)
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--force", action="store_true")

    install_p = sub.add_parser("install")
    add_common(install_p, artifact=True)

    update_p = sub.add_parser("update")
    add_common(update_p, artifact=True)

    uninstall_p = sub.add_parser("uninstall")
    add_common(uninstall_p)
    uninstall_p.add_argument("--dry-run", action="store_true")
    uninstall_p.add_argument("--yes", action="store_true")

    doctor_p = sub.add_parser("doctor")
    add_common(doctor_p)
    doctor_p.add_argument("--online", action="store_true")

    list_p = sub.add_parser("list-blenders")
    add_common(list_p)

    sub.add_parser("version")
    sub.add_parser("help")

    return parser


def _print(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2))
        return
    for key, value in result.items():
        print(f"{key}: {value}")


def _print_help() -> None:
    print("blender-mobile-3d commands:")
    for name in ("install", "update", "uninstall", "doctor", "list-blenders", "version", "help"):
        print(f"  {name}")


def _dispatch(ns: argparse.Namespace) -> dict:
    if ns.command == "install":
        return installer.do_install(
            explicit_blender=ns.blender,
            version=ns.addon_version,
            manifest_url=ns.manifest_url,
            offline_zip=ns.offline_zip,
            dry_run=ns.dry_run,
            force=ns.force,
        )
    if ns.command == "update":
        return installer.do_update(
            explicit_blender=ns.blender,
            version=ns.addon_version,
            manifest_url=ns.manifest_url,
            offline_zip=ns.offline_zip,
            dry_run=ns.dry_run,
            force=ns.force,
        )
    if ns.command == "uninstall":
        return installer.do_uninstall(explicit_blender=ns.blender, dry_run=ns.dry_run, yes=ns.yes)
    if ns.command == "doctor":
        return installer.do_doctor(
            explicit_blender=ns.blender,
            check_online=ns.online,
            installer_version=DEFAULT_ADDON_VERSION,
        )
    if ns.command == "list-blenders":
        return installer.do_list_blenders(explicit_blender=ns.blender)
    raise AssertionError(f"unreachable command: {ns.command}")  # pragma: no cover


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    parser = _build_parser()
    try:
        ns = parser.parse_args(args)
    except InstallerError as exc:
        print(f"error: {exc.message}", file=sys.stderr)
        parser.print_usage(sys.stderr)
        return exc.exit_code

    if ns.command is None or ns.command == "help":
        _print_help()
        return SUCCESS
    if ns.command == "version":
        print(INSTALLER_VERSION)
        return SUCCESS

    try:
        result = _dispatch(ns)
    except InstallerError as exc:
        if ns.json:
            print(json.dumps({"ok": False, "error": exc.message, "exit_code": exc.exit_code}))
        else:
            print(f"error: {exc.message}", file=sys.stderr)
        return exc.exit_code

    _print(result, ns.json)

    if ns.command == "doctor" and not result.get("ok", True):
        if not result.get("tmp_dir_writable", True):
            return PERMISSION_FAILURE
        return BLENDER_NOT_FOUND

    return SUCCESS


if __name__ == "__main__":
    sys.exit(main())
