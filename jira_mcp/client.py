"""Async Jira Cloud REST API v3 client (HTTP Basic auth).

Reads credentials from environment:
- JIRA_SITE   e.g. "your-company" for https://your-company.atlassian.net
- JIRA_EMAIL  Atlassian account email
- JIRA_API_TOKEN  API token from https://id.atlassian.com/manage-profile/security/api-tokens
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class JiraConfigError(RuntimeError):
    """Raised when required Jira env vars are missing."""


class JiraAPIError(RuntimeError):
    """Raised when Jira responds with an error. Message is surfaced to the LLM."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"Jira API {status}: {message}")
        self.status = status
        self.message = message


def _base_url() -> str:
    site = os.environ.get("JIRA_SITE")
    if not site:
        raise JiraConfigError("JIRA_SITE env var is required (the subdomain before .atlassian.net).")
    site = site.strip().removeprefix("https://").removesuffix(".atlassian.net")
    return f"https://{site}.atlassian.net"


def _auth() -> tuple[str, str]:
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not email or not token:
        raise JiraConfigError("JIRA_EMAIL and JIRA_API_TOKEN env vars are required.")
    return email, token


def _client(*, base: str | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base or _base_url(),
        auth=_auth(),
        headers={"Accept": "application/json"},
        timeout=30.0,
    )


def _extract_error(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except Exception:
        return resp.text[:500] or resp.reason_phrase
    msgs: list[str] = []
    if isinstance(data, dict):
        for key in ("errorMessages", "warningMessages"):
            v = data.get(key)
            if isinstance(v, list):
                msgs.extend(str(x) for x in v)
        errors = data.get("errors")
        if isinstance(errors, dict):
            msgs.extend(f"{k}: {v}" for k, v in errors.items())
    return "; ".join(msgs) or resp.text[:500] or resp.reason_phrase


async def request(
    method: str,
    path: str,
    *,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Any:
    """Issue a request against /rest/api/3 (path may also be absolute starting with /rest/...)."""
    if not path.startswith("/rest/"):
        path = f"/rest/api/3{path}"
    headers = dict(extra_headers or {})
    async with _client() as client:
        resp = await client.request(
            method,
            path,
            json=json,
            params=params,
            files=files,
            headers=headers,
        )
    if resp.status_code >= 400:
        raise JiraAPIError(resp.status_code, _extract_error(resp))
    if resp.status_code == 204 or not resp.content:
        return None
    ctype = resp.headers.get("content-type", "")
    if "application/json" in ctype:
        return resp.json()
    return resp.text
