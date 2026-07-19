"""Versioned preset and schema loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blender_mobile_3d.core.errors import ConfigurationError


DEFAULT_PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "presets"
DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "schemas" / "preset.schema.json"


def load_preset(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ConfigurationError(f"Preset not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    schema_version = str(data.get("schema_version", ""))
    if schema_version != "1.0.0":
        raise ConfigurationError(f"Unsupported preset schema_version: {schema_version}")
    return data


def available_presets(presets_dir: Path = DEFAULT_PRESETS_DIR) -> list[str]:
    return [p.stem for p in presets_dir.glob("*.json")]
