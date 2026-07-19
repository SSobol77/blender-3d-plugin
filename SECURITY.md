# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

Report security issues by opening a private issue in this repository or by contacting the maintainer directly.

Please include:
- affected version or commit;
- reproduction steps;
- impact assessment;
- suggested remediation if available.

We will acknowledge reports promptly and coordinate a fix before public disclosure.

## Security Boundaries

- Default `blender-mcp` exposure is localhost-only.
- Agent-supplied code runs with the same permissions as Blender or Python.
- Malicious `.blend` files may execute embedded Python on open.
- Path validation prevents output outside project-root exports.
- Manifest hashes verify exported files, but they do not authenticate sources.

## Limitations

This plugin does not sandbox Blender, Python, or the host filesystem. Treat untrusted assets and configurations as executable content.
