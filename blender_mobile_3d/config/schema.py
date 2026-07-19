"""Preset schema validation helpers.

Validation is fail-closed: a missing validator, a missing or malformed
schema file, or invalid data all raise ``ConfigurationError``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blender_mobile_3d.core.errors import ConfigurationError

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    jsonschema = None  # type: ignore[assignment]

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_LOCATIONS = (
    # Inside the packaged add-on (release ZIP layout).
    _PACKAGE_ROOT / "schemas" / "preset.schema.json",
    # Repository checkout layout.
    _PACKAGE_ROOT.parent / "schemas" / "preset.schema.json",
)


def default_schema_path() -> Path:
    """Return the first preset schema location that exists (or the last candidate)."""
    for candidate in _SCHEMA_LOCATIONS:
        if candidate.exists():
            return candidate
    return _SCHEMA_LOCATIONS[-1]


DEFAULT_SCHEMA_PATH = default_schema_path()


def validate_preset_schema(data: Any, schema_path: Path | None = None) -> None:
    """Validate ``data`` against the preset JSON Schema.

    Raises ConfigurationError when the validator is unavailable, the schema
    file is missing or malformed, the JSON root is not an object, or the
    data violates the schema.
    """
    if jsonschema is None:
        raise ConfigurationError(
            "jsonschema is required for preset validation but is not installed."
        )

    resolved = Path(schema_path) if schema_path is not None else default_schema_path()
    if not resolved.exists():
        raise ConfigurationError(f"Preset schema not found: {resolved}")

    try:
        with resolved.open("r", encoding="utf-8") as f:
            schema = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Preset schema unreadable or malformed: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigurationError(f"Preset root must be a JSON object, got {type(data).__name__}.")

    try:
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.SchemaError as exc:
        raise ConfigurationError(f"Preset schema is invalid: {exc.message}") from exc
    except jsonschema.exceptions.ValidationError as exc:
        raise ConfigurationError(f"Preset schema validation failed: {exc.message}") from exc
