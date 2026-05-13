"""FastMCP server exposing Jira Cloud actions as tools.

The actual tool implementations live in `tools.py`; this file just registers
them with FastMCP. Tool docstrings are the LLM-facing descriptions.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import tools
# Re-export tool functions at module level for convenient access (and tests).
from .tools import (  # noqa: F401
    add_attachment,
    add_comment,
    assign_issue,
    get_current_user,
    get_issue,
    link_issues,
    list_attachments,
    list_issue_link_types,
    list_projects,
    list_transitions,
    search_issues,
    search_users,
    transition_issue,
    update_issue,
)

mcp = FastMCP("jira")

# Register every tool from tools.ALL_TOOLS with FastMCP. Using @mcp.tool()
# preserves the function's name, signature, and docstring.
for _name, _fn in tools.ALL_TOOLS.items():
    mcp.tool()(_fn)
