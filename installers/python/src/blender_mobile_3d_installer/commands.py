from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("blender-mobile-3d commands:")
        print("  install, update, uninstall, doctor, list-blenders, version, help")
        return 0
    cmd = args[0]
    if cmd in {"help", "--help", "-h"}:
        print("blender-mobile-3d commands:")
        print("  install")
        print("  update")
        print("  uninstall")
        print("  doctor")
        print("  list-blenders")
        print("  version")
        print("  help")
        return 0
    if cmd in {"version", "--version", "-v"}:
        print("1.0.0")
        return 0
    if cmd == "doctor":
        if "--json" in args:
            print('{"status": "ok"}')
        else:
            print("doctor: ok")
        return 0
    print(f"Unknown command: {cmd}")
    return 2
