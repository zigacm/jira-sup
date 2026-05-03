# jira-mcp

A local MCP (Model Context Protocol) server that exposes Jira Cloud actions as
tools to VS Code Copilot Chat — built for Project Manager workflows on Jira
Service Management.

## Tools

Read helpers: `get_current_user`, `list_projects`, `search_users`,
`list_transitions`, `list_issue_link_types`.

Actions: `search_issues` (JQL), `get_issue`, `add_comment`, `transition_issue`
(close/move), `assign_issue`, `update_issue`, `link_issues`, `add_attachment`,
`list_attachments`.

## Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`
- A Jira Cloud API token: <https://id.atlassian.com/manage-profile/security/api-tokens>

## Install

```bash
cd "~/Documents/JIRA SUP"
uv sync
```

## Configure

Copy `.env.example` to `.env` and fill in:

```env
JIRA_SITE=your-company        # subdomain only (your-company.atlassian.net)
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
```

## Run / inspect locally

```bash
uv run python -m jira_mcp                       # starts stdio MCP server
npx @modelcontextprotocol/inspector uv run python -m jira_mcp   # interactive UI
```

## Register in VS Code

Add the contents of `.vscode/mcp.json` (created in this repo) to your workspace
or your user-level `mcp.json`. The API token is requested at first launch and
stored in VS Code's secret storage — it is never written to the JSON file.

Open Copilot Chat → switch to **Agent** mode → the `jira` tools and the
**Jira PM** chat mode appear.

## Tests

```bash
uv sync --extra dev
uv run pytest
```

## Notes

- "Closing" a ticket = a workflow transition. Use `list_transitions` first if
  you don't know the exact name (varies per project workflow).
- Comments use Atlassian Document Format (ADF); plain text is wrapped automatically.
- `search_issues` uses the new `POST /rest/api/3/search/jql` endpoint (the
  legacy `/search` was deprecated in May 2025).
