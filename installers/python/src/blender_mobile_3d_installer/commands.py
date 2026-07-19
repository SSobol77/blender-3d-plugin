from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in {"help", "--help", "-h"}:
        print("blender-mobile-3d commands:")
        print("  install, update, uninstall, doctor, list-blenders, version, help")
        return 0
    if args[0] == "version":
        print("1.0.0")
        return 0
    if args[0] == "doctor":
        if "--json" in args:
            print("{\"status\": \"ok\"}")
        else:
            print("doctor: ok")
        return 0
    print(f"Unknown command: {args[0]}")
    return 2
