"""Versioned preset loader with structural and schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blender_mobile_3d.config import schema as _schema
from blender_mobile_3d.core.errors import ConfigurationError

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_PRESET_LOCATIONS = (
    # Inside the packaged add-on (release ZIP layout).
    _PACKAGE_ROOT / "presets",
    # Repository checkout layout.
    _PACKAGE_ROOT.parent / "presets",
)

_REQUIRED_SECTIONS = ("limits", "paths", "export")


def default_presets_dir() -> Path:
    """Return the first presets directory that exists (or the last candidate)."""
    for candidate in _PRESET_LOCATIONS:
        if candidate.is_dir():
            return candidate
    return _PRESET_LOCATIONS[-1]


DEFAULT_PRESETS_DIR = default_presets_dir()


def load_preset(path: str | Path) -> dict[str, Any]:
    """Load and validate a preset file; raises ConfigurationError on any defect."""
    path = Path(path)
    if not path.exists():
        raise ConfigurationError(f"Preset not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Preset unreadable or malformed: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigurationError(f"Preset root must be a JSON object, got {type(data).__name__}.")

    schema_version = str(data.get("schema_version", ""))
    if schema_version != "1.0.0":
        raise ConfigurationError(f"Unsupported preset schema_version: {schema_version}")

    for section in _REQUIRED_SECTIONS:
        if not isinstance(data.get(section), dict):
            raise ConfigurationError(f"Preset section missing or not an object: {section}")

    # Strict JSON Schema validation runs whenever the validator is
    # available (always, outside Blender's bundled interpreter).
    if _schema.jsonschema is not None:
        _schema.validate_preset_schema(data)

    return data


def available_presets(presets_dir: Path | None = None) -> list[str]:
    target = Path(presets_dir) if presets_dir is not None else default_presets_dir()
    return [p.stem for p in target.glob("*.json")]
