# How to use the Jira agent

A short, practical guide for using the local Jira MCP server from VS Code Copilot Chat.

---

## 1. What it is

A local **MCP server** (`jira-mcp`) that gives Copilot Chat a set of Jira tools
(search issues, comment, transition, assign, link, attach, etc.) so you can
manage your Service Desk queue by chatting in natural language.

- Auth: your Atlassian email + API token (stored locally in `.env`).
- Site: `comtradegaming.atlassian.net`.
- Project used: **CGG** (Comtradegaming Service Desk).

---

## 2. One-time setup (already done)

✅ `.env` created with `JIRA_SITE`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
✅ Dependencies installed via `uv sync`
✅ MCP server registered in `.vscode/mcp.json`

If you ever rotate the token: edit `.env` and restart the MCP server in VS Code
(Command Palette → **MCP: Restart Server**).

---

## 3. Start using it

1. Open this folder in VS Code.
2. Open **Copilot Chat** (sidebar).
3. Switch the chat dropdown to **Agent** mode.
4. Make sure the `jira` server is enabled (tools icon → check `jira`).
5. Just ask, in plain English.

---

## 4. Example prompts

Read / search:
- "Show my open CGG tickets, newest first."
- "Find CGG tickets with status 'Waiting for support'."
- "Summarize CGG-258."
- "What transitions are available on CGG-255?"

Write / act:
- "Add a comment on CGG-258: 'Forwarded to SOFTSWISS, awaiting response.'"
- "Move CGG-256 to Resolved."
- "Assign CGG-257 to me."
- "Link CGG-258 as 'Relates' to CGG-255."
- "Attach `report.pdf` to CGG-254."

The agent will pick the right tool, ask for confirmation on destructive
actions, and show you the result.

---

## 5. Available tools (what the agent can do)

**Read helpers**
- `get_current_user` — who am I
- `list_projects` — list/search projects
- `search_users` — find a user (to get accountId for assigning)
- `list_transitions` — workflow steps available on an issue
- `list_issue_link_types` — valid link types (Blocks, Relates, …)

**Actions**
- `search_issues` — JQL search
- `get_issue` — full details for one issue
- `add_comment` — post a comment (plain text auto-wrapped to ADF)
- `transition_issue` — close / move an issue (e.g. "Resolve this issue")
- `assign_issue` — assign to a user (or "me")
- `update_issue` — edit fields (summary, description, priority, …)
- `link_issues` — create a link between two issues
- `add_attachment` / `list_attachments` — file attachments

---

## 6. Useful JQL snippets

| Goal | JQL |
|---|---|
| My open tickets | `project = CGG AND assignee = currentUser() AND statusCategory != Done` |
| Newest in queue | `project = CGG ORDER BY created DESC` |
| Waiting on customer | `project = CGG AND status = "Waiting for customer"` |
| Resolved this week | `project = CGG AND resolved >= startOfWeek()` |
| Unassigned | `project = CGG AND assignee is EMPTY` |

You can paste any of these into a prompt: *"Run this JQL: …"*.

---

## 7. Troubleshooting

- **"Tool not found" / `jira` missing in Copilot:** Command Palette →
  **MCP: List Servers** → restart `jira`.
- **401 / 403 errors:** token expired or revoked → generate a new one at
  <https://id.atlassian.com/manage-profile/security/api-tokens>, update `.env`,
  restart the server.
- **Wrong transition name:** ask the agent "list transitions for CGG-XXX"
  first — workflows differ per project.
- **Verify auth manually:**
  ```bash
  cd "~/Documents/JIRA SUP"
  .venv/bin/python -c "from dotenv import load_dotenv; load_dotenv(); \
    import asyncio; from jira_mcp.client import request; \
    print(asyncio.run(request('GET','/myself'))['displayName'])"
  ```

---

## 8. Safety notes

- `.env` is gitignored — do not commit it.
- Never paste your API token into chat or share it in screenshots.
- The agent will confirm before destructive actions, but always double-check
  the issue key before approving a transition or comment.
