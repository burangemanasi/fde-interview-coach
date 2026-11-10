"""PreToolUse hook: block Claude Code from reading .env files.

Claude Code pipes the pending tool call to stdin as JSON, e.g.
    {"tool_name": "Read", "tool_input": {"file_path": "C:/.../my-coach/.env"}, ...}

Exit codes:
    0 -> allow the read
    2 -> block it; whatever we print to stderr is shown to Claude as the reason
"""
from __future__ import annotations

import json
import sys

ALLOWED = ".env.example"  # the template is safe to read: it holds no secrets


def is_blocked(file_path: str) -> bool:
    """True for any path that looks like a .env file, except the .env.example template."""
    path = file_path.lower()  # Windows paths are case-insensitive: .ENV is still .env
    return ".env" in path and ALLOWED not in path


def main() -> int:
    event = json.load(sys.stdin)
    file_path = event.get("tool_input", {}).get("file_path", "")
    if is_blocked(file_path):
        print(
            f"Blocked: reading '{file_path}' is not allowed - .env files hold secrets. "
            "Read .env.example to see which settings exist.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
