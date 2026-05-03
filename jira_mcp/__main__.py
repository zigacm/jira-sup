"""Entrypoint: `python -m jira_mcp` runs the MCP server over stdio."""

from __future__ import annotations

from dotenv import load_dotenv

from .server import mcp


def main() -> None:
    load_dotenv()
    mcp.run()


if __name__ == "__main__":
    main()
