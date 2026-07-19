"""Preset schema validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blender_mobile_3d.core.errors import ConfigurationError

try:
    import jsonschema  # optional dependency
except Exception:  # pragma: no cover
    jsonschema = None

DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent / "schemas" / "preset.schema.json"
)


def validate_preset_schema(data: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA_PATH) -> None:
    if jsonschema is None:
        return
    if not schema_path.exists():
        return

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        jsonschema.validate(data, schema)
    except Exception as exc:  # pragma: no cover - optional dep paths
        raise ConfigurationError(f"Preset schema validation failed: {exc}") from exc
