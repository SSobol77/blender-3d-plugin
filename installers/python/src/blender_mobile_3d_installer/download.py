"""Secure artifact download: HTTPS-or-loopback, bounded size, atomic rename."""

from __future__ import annotations

import hashlib
import tempfile
import urllib.request
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse

from blender_mobile_3d_installer.exit_codes import (
    CHECKSUM_MISMATCH,
    DOWNLOAD_FAILURE,
    InstallerError,
)

DOWNLOAD_TIMEOUT_SECONDS = 60
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _require_https_or_loopback(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in _LOOPBACK_HOSTS:
        return
    raise InstallerError(
        DOWNLOAD_FAILURE,
        f"Refusing non-HTTPS download URL (loopback exempt for testing only): {url}",
    )


def download_artifact(
    url: str,
    dest_path: Path,
    expected_sha256: str,
    max_size_bytes: int,
) -> Path:
    """Download ``url`` to ``dest_path``, verifying size and checksum.

    Writes to a temporary file in the destination's own directory and
    performs an atomic rename only after the checksum matches. Any failure
    removes the partial file and raises InstallerError.
    """
    _require_https_or_loopback(url)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    digest = hashlib.sha256()
    total = 0
    tmp_fd, tmp_name = tempfile.mkstemp(
        dir=str(dest_path.parent), prefix=".download-", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        try:
            # Scheme already restricted to https (or loopback http for tests)
            # by _require_https_or_loopback above.
            request = urllib.request.Request(  # noqa: S310
                url, headers={"User-Agent": "blender-mobile-3d-installer"}
            )
            with (
                urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response,  # noqa: S310
                open(tmp_fd, "wb") as tmp_file,
            ):
                while True:
                    chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_size_bytes:
                        raise InstallerError(
                            DOWNLOAD_FAILURE,
                            f"Download from {url} exceeded the {max_size_bytes}-byte limit.",
                        )
                    digest.update(chunk)
                    tmp_file.write(chunk)
        except (URLError, TimeoutError, OSError) as exc:
            raise InstallerError(DOWNLOAD_FAILURE, f"Download failed for {url}: {exc}") from exc

        if total == 0:
            raise InstallerError(DOWNLOAD_FAILURE, f"Download from {url} was empty.")

        actual = digest.hexdigest()
        if actual != expected_sha256:
            raise InstallerError(
                CHECKSUM_MISMATCH,
                f"Checksum mismatch for {url}: expected {expected_sha256}, got {actual}.",
            )

        tmp_path.replace(dest_path)
        return dest_path
    finally:
        tmp_path.unlink(missing_ok=True)
