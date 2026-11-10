"""MCP server "interview-guides": serves the markdown guides in resources/.

MCP (Model Context Protocol) lets an AI agent pull in data that lives outside
the conversation. Here Claude can list the interview guides and fetch one on
demand, instead of us pasting guidance into a prompt.

Run it (from my-coach/):
    .venv\\Scripts\\python.exe mcp/server.py
Poke at it in a UI:
    npx @modelcontextprotocol/inspector .venv\\Scripts\\python.exe mcp/server.py
"""
from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# The guides live in my-coach/resources/ (this file is my-coach/mcp/server.py).
RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"

mcp = FastMCP("interview-guides")


def _guide_paths() -> dict[str, Path]:
    """Map each guide name (file name without .md) to its path."""
    return {path.stem: path for path in sorted(RESOURCES_DIR.glob("*.md"))}


@mcp.tool
def list_guides() -> list[str]:
    """List the available interview guide names, e.g. 'decomposition-guide'."""
    return list(_guide_paths())


@mcp.tool
def get_guide(name: str) -> str:
    """Return the full markdown of one interview guide.

    `name` is a value from list_guides(), e.g. 'system-design-guide'
    (a trailing '.md' is accepted too).
    """
    guides = _guide_paths()
    # Look the name up among real guides rather than building a path from it,
    # so a name like '../.env' can never reach a file outside resources/.
    path = guides.get(name.removesuffix(".md"))
    if path is None:
        available = ", ".join(guides) or "(none)"
        raise ToolError(f"No guide named '{name}'. Available guides: {available}")
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()  # stdio transport: Claude Code launches this as a subprocess
