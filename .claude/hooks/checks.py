"""PostToolUse hook: lint and type-check after Claude edits Python code.

Claude Code pipes the finished tool call to stdin as JSON, e.g.
    {"tool_name": "Edit", "tool_input": {"file_path": "C:/.../my-coach/app/main.py", ...}, ...}

Runs `ruff check app tests` and `mypy app`, but only when the edited file is a .py
file under app/ or tests/ - editing a markdown file shouldn't cost a mypy run.

Exit codes:
    0 -> checks passed (or skipped)
    2 -> a check failed; the output goes to stderr, where both you and Claude see it
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# my-coach/ : Claude Code sets CLAUDE_PROJECT_DIR; fall back to this file's location.
PROJECT_DIR = Path(
    os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2]
).resolve()

CHECKED_FOLDERS = ("app", "tests")
CHECKS = [
    ["ruff", "check", "app", "tests"],
    ["mypy", "app"],
]


def project_python() -> str:
    """The project's venv interpreter (where ruff/mypy are installed), else this one."""
    for candidate in (
        PROJECT_DIR / ".venv" / "Scripts" / "python.exe",  # Windows
        PROJECT_DIR / ".venv" / "bin" / "python",  # macOS/Linux
    ):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def touched_python_code(file_path: str) -> bool:
    """True if the edited file is a .py file inside app/ or tests/."""
    path = Path(file_path)
    if path.suffix != ".py":
        return False
    try:
        relative = path.resolve().relative_to(PROJECT_DIR)
    except ValueError:  # outside the project
        return False
    return relative.parts[0] in CHECKED_FOLDERS


def main() -> int:
    event = json.load(sys.stdin)
    file_path = event.get("tool_input", {}).get("file_path", "")
    if not touched_python_code(file_path):
        return 0

    python = project_python()
    failures = []
    for check in CHECKS:  # run both, so one round shows every problem
        result = subprocess.run(
            [python, "-m", *check], cwd=PROJECT_DIR, capture_output=True, text=True
        )
        if result.returncode != 0:
            failures.append(f"$ {' '.join(check)}\n{result.stdout}{result.stderr}".rstrip())

    if failures:
        print("Checks failed after this edit:\n\n" + "\n\n".join(failures), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
