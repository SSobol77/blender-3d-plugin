"""Blender-MCP adapter utilities."""

from __future__ import annotations

import os

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


def default_socket_path() -> str:
    host = os.environ.get("BM3D_MCP_HOST", DEFAULT_HOST)
    port = os.environ.get("BM3D_MCP_PORT", str(DEFAULT_PORT))
    return f"{host}:{port}"
