"""Agent adapter documentation instead of separate implementations."""

from __future__ import annotations

AGENT_NOTES = {
    "hermes": "Use blender-mcp execute_code or shell against localhost:9876.",
    "claude_code": "Use the terminal tool; drive Blender CLI or Python scripts.",
    "codex": "Use run or shell; call scripts/blender_mobile_3d_cli.py from the repo root.",
    "kimi": "Use bash or direct TCP adapter calls to blender-mcp with the same core operators.",
}


def notes_for(agent: str) -> str:
    return AGENT_NOTES.get(agent, "Use Blender CLI or background Python workflows.")
