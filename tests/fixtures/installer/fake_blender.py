#!/usr/bin/env python3
"""Fake Blender executable for fast installer unit tests (no real bpy).

Controlled entirely via environment variables so tests can simulate any
discovery/orchestration scenario without launching real Blender:

- FAKE_BLENDER_VERSION: version string printed for ``--version`` (default 4.9.0)
- FAKE_BLENDER_RESPONSES: JSON object mapping action -> response dict, used
  for the ``--python blender_helper.py -- <json>`` invocation style
- FAKE_BLENDER_EXIT_CODE: process exit code for the helper invocation
"""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    if "--version" in sys.argv:
        version = os.environ.get("FAKE_BLENDER_VERSION", "4.9.0")
        print(f"Blender {version} (hash deadbeef built 2026-01-01 00:00:00)")
        return 0

    if "--" in sys.argv:
        request = json.loads(sys.argv[sys.argv.index("--") + 1])
        action = request.get("action", "")
        responses = json.loads(os.environ.get("FAKE_BLENDER_RESPONSES", "{}"))
        result = responses.get(action, {"ok": True})
        print(json.dumps(result))
        return int(os.environ.get("FAKE_BLENDER_EXIT_CODE", "0"))

    return 1


if __name__ == "__main__":
    sys.exit(main())
