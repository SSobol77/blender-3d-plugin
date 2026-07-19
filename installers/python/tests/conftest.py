"""Shared fixtures for installer tests: fake Blender executable, HTTP server."""

from __future__ import annotations

import http.server
import json
import shutil
import stat
import threading
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "installer"


@pytest.fixture
def fake_blender(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Copy fake_blender.py to a controllable path and set env hooks for it."""
    target = tmp_path / "blender"
    shutil.copy(FIXTURES_DIR / "fake_blender.py", target)
    target.chmod(target.stat().st_mode | stat.S_IEXEC)

    def _configure(*, version: str = "4.9.0", responses: dict | None = None, exit_code: int = 0):
        monkeypatch.setenv("FAKE_BLENDER_VERSION", version)
        monkeypatch.setenv("FAKE_BLENDER_RESPONSES", json.dumps(responses or {}))
        monkeypatch.setenv("FAKE_BLENDER_EXIT_CODE", str(exit_code))
        return str(target)

    return _configure


class _FixtureHTTPServer(http.server.ThreadingHTTPServer):
    daemon_threads = True


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        pass


@pytest.fixture
def http_fixture_server(tmp_path: Path):
    """Serve tmp_path over HTTP on 127.0.0.1; yields (base_url, directory)."""
    directory = tmp_path / "www"
    directory.mkdir()

    def handler_factory(*args: Any, **kwargs: Any) -> _QuietHandler:
        return _QuietHandler(*args, directory=str(directory), **kwargs)

    server = _FixtureHTTPServer(("127.0.0.1", 0), handler_factory)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        yield base_url, directory
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
