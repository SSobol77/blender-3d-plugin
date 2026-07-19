"""Custom exceptions for blender_mobile_3d."""

from __future__ import annotations


class BlenderMobileError(Exception):
    """Base error."""


class ConfigurationError(BlenderMobileError):
    """Invalid preset/config."""


class ValidationError(BlenderMobileError):
    """Asset validation failure."""


class ExportError(BlenderMobileError):
    """Export failure."""


class PathSafetyError(BlenderMobileError):
    """Unsafe output path."""
