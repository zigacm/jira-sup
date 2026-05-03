"""FastMCP server exposing Jira Cloud actions as tools.

Tool docstrings are the LLM-facing descriptions. Keep them precise.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import client as jira
from .adf import text_to_adf

mcp = FastMCP("jira")


# ---------------------------------------------------------------------------
# Read-only helpers (call these first when unsure about IDs / names).
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_current_user() -> dict[str, Any]:
    """Return the currently authenticated Jira user (accountId, displayName, emailAddress).

    Use this to resolve "me" / "assign to me" / "my tickets".
    """
    return await jira.request("GET", "/myself")


@mcp.tool()
async def list_projects(query: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List Jira projects (optionally filtered by name/key substring).

    Returns a list of {id, key, name, projectTypeKey}.
    """
    params: dict[str, Any] = {"maxResults": limit}
    if query:
        params["query"] = query
    data = await jira.request("GET", "/project/search", params=params)
    values = (data or {}).get("values", [])
    return [
        {
            "id": p.get("id"),
            "key": p.get("key"),
            "name": p.get("name"),
            "projectTypeKey": p.get("projectTypeKey"),
        }
        for p in values
    ]


@mcp.tool()
async def search_users(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Jira users by name or email. Returns [{accountId, displayName, emailAddress, active}].

    Use this to resolve a human-readable name to an accountId before assigning.
    """
    data = await jira.request(
        "GET", "/user/search", params={"query": query, "maxResults": limit}
    )
    return [
        {
            "accountId": u.get("accountId"),
            "displayName": u.get("displayName"),
            "emailAddress": u.get("emailAddress"),
            "active": u.get("active"),
        }
        for u in (data or [])
    ]


@mcp.tool()
async def list_transitions(issue_key: str) -> list[dict[str, Any]]:
    """List workflow transitions available on an issue right now.

    Call this BEFORE `transition_issue` to learn the exact transition name to use
    (workflows differ per project — "Done", "Close Issue", "Resolve", etc.).
    """
    data = await jira.request("GET", f"/issue/{issue_key}/transitions")
    return [
        {
            "id": t.get("id"),
            "name": t.get("name"),
            "to_status": (t.get("to") or {}).get("name"),
        }
        for t in (data or {}).get("transitions", [])
    ]


@mcp.tool()
async def list_issue_link_types() -> list[dict[str, Any]]:
    """List valid issue link types (e.g. "Blocks", "Relates", "Duplicate").

    Call before `link_issues` so you pass a valid `link_type`.
    """
    data = await jira.request("GET", "/issueLinkType")
    return [
        {"id": t.get("id"), "name": t.get("name"), "inward": t.get("inward"), "outward": t.get("outward")}
        for t in (data or {}).get("issueLinkTypes", [])
    ]


# ---------------------------------------------------------------------------
# Core actions.
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_issues(
    jql: str,
    fields: list[str] | None = None,
    limit: int = 25,
    next_page_token: str | None = None,
) -> dict[str, Any]:
    """Search Jira issues with JQL.

    Args:
        jql: A JQL expression, e.g. `project = SUP AND status != Done ORDER BY created DESC`.
        fields: Field names to return (default: summary, status, assignee, priority, updated).
        limit: Max issues per page (Jira caps at 100 for the new endpoint).
        next_page_token: Pass `nextPageToken` from a prior response to paginate.

    Uses POST /rest/api/3/search/jql (the legacy /search endpoint was deprecated in May 2025).
    """
    body: dict[str, Any] = {
        "jql": jql,
        "maxResults": min(max(limit, 1), 100),
        "fields": fields or ["summary", "status", "assignee", "priority", "updated"],
    }
    if next_page_token:
        body["nextPageToken"] = next_page_token
    data = await jira.request("POST", "/search/jql", json=body)
    issues = []
    for issue in (data or {}).get("issues", []):
        f = issue.get("fields", {}) or {}
        issues.append(
            {
                "key": issue.get("key"),
                "id": issue.get("id"),
                "summary": f.get("summary"),
                "status": (f.get("status") or {}).get("name"),
                "assignee": (f.get("assignee") or {}).get("displayName") if f.get("assignee") else None,
                "priority": (f.get("priority") or {}).get("name") if f.get("priority") else None,
                "updated": f.get("updated"),
                "fields": f,
            }
        )
    return {
        "issues": issues,
        "nextPageToken": (data or {}).get("nextPageToken"),
        "isLast": (data or {}).get("isLast", True),
    }


@mcp.tool()
async def get_issue(issue_key: str, fields: list[str] | None = None) -> dict[str, Any]:
    """Fetch a single issue by key (e.g. "SUP-123"). Optionally restrict returned fields."""
    params: dict[str, Any] = {}
    if fields:
        params["fields"] = ",".join(fields)
    return await jira.request("GET", f"/issue/{issue_key}", params=params)


@mcp.tool()
async def add_comment(issue_key: str, body: str) -> dict[str, Any]:
    """Add a comment to an issue. `body` is plain text; it's wrapped into ADF automatically."""
    payload = {"body": text_to_adf(body)}
    return await jira.request("POST", f"/issue/{issue_key}/comment", json=payload)


@mcp.tool()
async def transition_issue(
    issue_key: str,
    transition_name: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """Move an issue through its workflow (this is how you "close" tickets in Jira).

    Args:
        issue_key: e.g. "SUP-123".
        transition_name: Case-insensitive name of the transition (e.g. "Done", "Close Issue").
            Call `list_transitions` first if unsure — workflows vary per project.
        comment: Optional plain-text comment to add atomically with the transition.
    """
    transitions = await jira.request("GET", f"/issue/{issue_key}/transitions")
    target = None
    for t in (transitions or {}).get("transitions", []):
        if (t.get("name") or "").lower() == transition_name.lower():
            target = t
            break
    if not target:
        available = [t.get("name") for t in (transitions or {}).get("transitions", [])]
        raise jira.JiraAPIError(
            400,
            f"No transition named {transition_name!r} on {issue_key}. Available: {available}",
        )

    payload: dict[str, Any] = {"transition": {"id": target["id"]}}
    if comment:
        payload["update"] = {"comment": [{"add": {"body": text_to_adf(comment)}}]}
    await jira.request("POST", f"/issue/{issue_key}/transitions", json=payload)
    return {
        "issue_key": issue_key,
        "transitioned_to": (target.get("to") or {}).get("name"),
        "transition_name": target.get("name"),
        "commented": bool(comment),
    }


@mcp.tool()
async def assign_issue(
    issue_key: str,
    account_id: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """Assign an issue to a user.

    Provide either `account_id` (preferred) OR `query` (a name/email substring; the
    first assignable match is used). Pass `account_id="-1"` to set default assignee,
    or `account_id=None` with no query to UNASSIGN.
    """
    resolved_id: str | None = account_id
    resolved_name: str | None = None

    if account_id is None and query:
        candidates = await jira.request(
            "GET",
            "/user/assignable/search",
            params={"query": query, "issueKey": issue_key, "maxResults": 5},
        )
        if not candidates:
            raise jira.JiraAPIError(404, f"No assignable user matched {query!r} for {issue_key}.")
        resolved_id = candidates[0].get("accountId")
        resolved_name = candidates[0].get("displayName")

    await jira.request(
        "PUT",
        f"/issue/{issue_key}/assignee",
        json={"accountId": resolved_id},
    )
    return {"issue_key": issue_key, "accountId": resolved_id, "displayName": resolved_name}


@mcp.tool()
async def update_issue(issue_key: str, fields: dict[str, Any]) -> dict[str, Any]:
    """Update issue fields (priority, labels, summary, duedate, customfield_*, etc.).

    Pass Jira's expected field shapes, e.g.:
        {"priority": {"name": "High"}}
        {"labels": ["billing", "urgent"]}
        {"summary": "New summary"}
        {"duedate": "2026-05-15"}
    For `description`, pass an ADF document or call `add_comment` for messages instead.
    """
    await jira.request("PUT", f"/issue/{issue_key}", json={"fields": fields})
    return {"issue_key": issue_key, "updated_fields": list(fields.keys())}


@mcp.tool()
async def link_issues(
    inward_key: str,
    outward_key: str,
    link_type: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """Create a link between two issues.

    Args:
        inward_key: The issue on the "inward" side of the relationship (e.g. the one being blocked).
        outward_key: The issue on the "outward" side (e.g. the blocker).
        link_type: A valid link type NAME (e.g. "Blocks", "Relates", "Duplicate").
            Call `list_issue_link_types` if unsure.
        comment: Optional plain-text comment posted on `inward_key` with the link.
    """
    payload: dict[str, Any] = {
        "type": {"name": link_type},
        "inwardIssue": {"key": inward_key},
        "outwardIssue": {"key": outward_key},
    }
    if comment:
        payload["comment"] = {"body": text_to_adf(comment)}
    await jira.request("POST", "/issueLink", json=payload)
    return {"inward": inward_key, "outward": outward_key, "type": link_type}


@mcp.tool()
async def add_attachment(issue_key: str, file_path: str) -> list[dict[str, Any]]:
    """Upload a local file as an attachment on an issue.

    `file_path` must be an absolute path readable by this server process.
    Returns metadata for the created attachment(s).
    """
    p = Path(file_path).expanduser()
    if not p.is_absolute():
        raise jira.JiraAPIError(400, "file_path must be absolute.")
    if not p.is_file():
        raise jira.JiraAPIError(404, f"File not found: {p}")
    # Defense-in-depth: refuse obvious sensitive paths.
    if str(p).startswith(("/etc/", "/private/etc/")) or p.name in {".env", "id_rsa", "id_ed25519"}:
        raise jira.JiraAPIError(400, f"Refusing to attach sensitive file: {p}")

    with p.open("rb") as fh:
        files = {"file": (p.name, fh.read(), "application/octet-stream")}
    data = await jira.request(
        "POST",
        f"/issue/{issue_key}/attachments",
        files=files,
        extra_headers={"X-Atlassian-Token": "no-check"},
    )
    return [
        {"id": a.get("id"), "filename": a.get("filename"), "size": a.get("size"), "mimeType": a.get("mimeType")}
        for a in (data or [])
    ]


@mcp.tool()
async def list_attachments(issue_key: str) -> list[dict[str, Any]]:
    """List attachments on an issue (id, filename, size, mimeType, author, created)."""
    issue = await jira.request("GET", f"/issue/{issue_key}", params={"fields": "attachment"})
    atts = ((issue or {}).get("fields") or {}).get("attachment") or []
    return [
        {
            "id": a.get("id"),
            "filename": a.get("filename"),
            "size": a.get("size"),
            "mimeType": a.get("mimeType"),
            "author": (a.get("author") or {}).get("displayName"),
            "created": a.get("created"),
        }
        for a in atts
    ]
