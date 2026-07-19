"""Manifest fetching and structural validation.

Deliberately does not depend on ``jsonschema``: the manifest shape is a
handful of fields, hand-validated identically to the Node installer so the
two frontends can never diverge on what they accept or reject (see
docs/installer-contract.md and tests/fixtures/installer/).
"""

from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError

from blender_mobile_3d_installer.exit_codes import MANIFEST_FAILURE, InstallerError

MANIFEST_MAX_BYTES = 1 * 1024 * 1024
MANIFEST_TIMEOUT_SECONDS = 15
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

DEFAULT_MANIFEST_URL_TEMPLATE = (
    "https://github.com/SSobol77/blender-3d-plugin/releases/download/"
    "v{version}/release-manifest.json"
)


@dataclass(frozen=True)
class ExtensionArtifact:
    filename: str
    url: str
    sha256: str
    size: int


@dataclass(frozen=True)
class Manifest:
    schema_version: str
    version: str
    minimum_blender_version: str | None
    maximum_blender_version_exclusive: str | None
    extension: ExtensionArtifact


def _require_https_or_loopback(url: str) -> None:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in _LOOPBACK_HOSTS:
        return
    raise InstallerError(
        MANIFEST_FAILURE,
        f"Refusing non-HTTPS URL (loopback exempt for testing only): {url}",
    )


def validate_manifest_structure(data: Any) -> Manifest:
    """Raise InstallerError(MANIFEST_FAILURE) on any structural defect."""
    if not isinstance(data, dict):
        raise InstallerError(MANIFEST_FAILURE, "Manifest root must be a JSON object.")

    if data.get("schema_version") != "1.0.0":
        raise InstallerError(
            MANIFEST_FAILURE,
            f"Unsupported manifest schema_version: {data.get('schema_version')!r}",
        )

    version = data.get("version")
    if not isinstance(version, str) or not _VERSION_RE.match(version):
        raise InstallerError(MANIFEST_FAILURE, f"Invalid manifest version: {version!r}")

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict) or not isinstance(artifacts.get("extension"), dict):
        raise InstallerError(MANIFEST_FAILURE, "Manifest missing artifacts.extension object.")

    ext = artifacts["extension"]
    filename = ext.get("filename")
    url = ext.get("url")
    sha256 = ext.get("sha256")
    size = ext.get("size")

    if not isinstance(filename, str) or not filename:
        raise InstallerError(MANIFEST_FAILURE, "Manifest extension.filename missing or invalid.")
    if not isinstance(url, str) or not url:
        raise InstallerError(MANIFEST_FAILURE, "Manifest extension.url missing or invalid.")
    if not isinstance(sha256, str) or not _SHA256_RE.match(sha256):
        raise InstallerError(MANIFEST_FAILURE, f"Manifest extension.sha256 invalid: {sha256!r}")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise InstallerError(MANIFEST_FAILURE, f"Manifest extension.size invalid: {size!r}")

    return Manifest(
        schema_version=data["schema_version"],
        version=version,
        minimum_blender_version=data.get("minimum_blender_version"),
        maximum_blender_version_exclusive=data.get("maximum_blender_version_exclusive"),
        extension=ExtensionArtifact(filename=filename, url=url, sha256=sha256, size=size),
    )


def fetch_manifest(version: str, manifest_url: str | None = None) -> Manifest:
    """Fetch and validate the manifest for ``version`` over the network."""
    url = manifest_url or DEFAULT_MANIFEST_URL_TEMPLATE.format(version=version)
    _require_https_or_loopback(url)

    # Scheme already restricted to https (or loopback http for tests) above.
    try:
        request = urllib.request.Request(  # noqa: S310
            url, headers={"User-Agent": "blender-mobile-3d-installer"}
        )
        with urllib.request.urlopen(request, timeout=MANIFEST_TIMEOUT_SECONDS) as response:  # noqa: S310
            raw = response.read(MANIFEST_MAX_BYTES + 1)
    except (URLError, TimeoutError, OSError) as exc:
        raise InstallerError(
            MANIFEST_FAILURE, f"Could not fetch manifest from {url}: {exc}"
        ) from exc

    if len(raw) > MANIFEST_MAX_BYTES:
        raise InstallerError(MANIFEST_FAILURE, f"Manifest at {url} exceeds the size limit.")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InstallerError(
            MANIFEST_FAILURE, f"Manifest at {url} is not valid JSON: {exc}"
        ) from exc

    return validate_manifest_structure(data)
