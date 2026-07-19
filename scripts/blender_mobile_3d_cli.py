#!/usr/bin/env python3
"""Background-mode CLI for blender_mobile_3d."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from blender_mobile_3d.config.loader import available_presets
from blender_mobile_3d.version import VERSION


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="blender_mobile_3d_cli")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list-presets")
    sub.add_parser("version")

    analyze = sub.add_parser("analyze")
    analyze.add_argument("--blend", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--manifest", required=True)

    print_schema = sub.add_parser("print-schema")
    print_schema.add_argument("--schema", required=False)

    args = parser.parse_args(argv)

    if args.command == "version":
        print(VERSION)
        return 0

    if args.command == "list-presets":
        print("\n".join(sorted(available_presets())))
        return 0

    if args.command == "print-schema":
        schema_path = (
            Path(args.schema)
            if args.schema
            else Path(__file__).resolve().parent.parent / "schemas" / "preset.schema.json"
        )
        print(schema_path.read_text(encoding="utf-8"))
        return 0

    if args.command == "validate":
        path = Path(args.manifest)
        if not path.exists():
            print(f"missing:{path}")
            return 2
        print(path.read_text(encoding="utf-8"))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
