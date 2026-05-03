# Jira PM Assistant — Getting Started

A step-by-step guide to set up and use your Jira MCP server inside VS Code Copilot Chat.

---

## 1. One-time setup (5 minutes)

### 1a. Get a Jira API token
1. Open <https://id.atlassian.com/manage-profile/security/api-tokens>
2. Click **Create API token** → label it `vscode-copilot` → **Copy** the token.
   - You'll see it only once. If you lose it, just create a new one.

### 1b. Open the project in VS Code
1. VS Code → **File → Open Folder…**
2. Choose `~/Documents/JIRA SUP`
3. If VS Code asks "Do you trust the authors?" — click **Yes** (it's your own folder).

### 1c. Verify dependencies are installed
Open a terminal in VS Code (`` Ctrl+` ``) and run:

```bash
uv sync
```

You should see no errors. (`uv` is already installed and on your PATH.)

### 1d. Reload VS Code so it sees the MCP server
- `Cmd+Shift+P` → type **Developer: Reload Window** → Enter.

---

## 2. First-run: connect to Jira (1 minute)

1. Open Copilot Chat (`Ctrl+Cmd+I` or click the chat icon in the side bar).
2. Switch the chat mode dropdown (top of the chat panel) to **Agent**.
3. Click the **tools** icon (🛠️) in the chat input → you should see a `jira` group with 14 tools. Make sure it's enabled.
4. The first time you send a message that uses Jira, VS Code will prompt for three values — fill them in **once**:

   | Prompt | Example | Notes |
   | --- | --- | --- |
   | `Jira site subdomain` | `acme` | Just the part before `.atlassian.net` |
   | `Atlassian account email` | `you@acme.com` | Your login email |
   | `Jira API token` | *(paste the token)* | Stored in VS Code's secret storage — never written to disk |

5. Switch the chat mode dropdown to **Jira PM** (this is the custom mode shipped in the project). It tells Copilot how to behave like your PM assistant.

You're done. Now talk to it in plain English.

---

## 3. Everyday usage — example prompts

Type these straight into the chat. Copilot will pick the right tool for you and ask before doing anything destructive.

### See your queue
> show me my open tickets, highest priority first

### Triage a project
> show all unassigned bugs in project SUP from the last 7 days

### Look up a ticket
> what's the status of SUP-142?

### Comment on a ticket
> comment on SUP-142: "Investigating with the platform team — ETA tomorrow."

### Close a ticket (with a resolution comment)
> close SUP-142 with comment "Fixed in release 4.7"

> The PM mode will always confirm the closing transition name (e.g. "Done", "Resolve") and the comment before executing.

### Reassign a ticket
> assign SUP-142 to Maria

> If multiple Marias exist, Copilot will list them and ask which one.

### Assign to yourself
> assign SUP-142 to me

### Change priority / labels
> set SUP-142 priority to High and add label "billing"

### Link two tickets
> mark SUP-142 as blocked by SUP-99

### Attach a file
> attach /Users/ziga/Desktop/error-log.txt to SUP-142

### Bulk operations (will ask for confirmation)
> close all tickets in project SUP with status "Waiting for Customer" older than 30 days, comment "Auto-closed: no response"

---

## 4. How it works (the 30-second version)

```
VS Code Copilot Chat  ──►  jira-mcp (local Python process)  ──►  Jira Cloud REST API
                              ▲
                              │  Started automatically when you chat;
                              │  reads your token from VS Code secret storage.
```

- **Tools** are 14 small Python functions (e.g. `add_comment`, `transition_issue`). Copilot picks which to call based on your request.
- **Jira PM chat mode** ([.github/chatmodes/jira-pm.chatmode.md](.github/chatmodes/jira-pm.chatmode.md)) is a system prompt that gives Copilot the PM-specific rules: always comment when closing, confirm bulk actions, default to "my queue", etc.
- Everything runs **locally on your Mac**. Nothing is sent anywhere except your direct calls to `*.atlassian.net`.

---

## 5. Tips for getting good results

1. **Always include the issue key** when you know it (`SUP-142`). It saves a search step.
2. **Be specific about scope** ("project SUP", "this sprint", "older than 7 days") — Copilot turns these into JQL.
3. **Trust the confirmation step.** When Copilot says *"I'm about to close 12 tickets — proceed?"*, read it before saying yes.
4. **If a transition name is wrong** (e.g. "Close" doesn't exist on a workflow), just ask: *"what transitions are available on SUP-142?"* — that calls `list_transitions`.
5. **Custom fields**: if you need to set one and don't know its ID, ask *"what fields does SUP-142 have?"* and Copilot will read them via `get_issue`.

---

## 6. Troubleshooting

| Problem | Fix |
| --- | --- |
| Tools don't appear in the picker | Reload window (`Cmd+Shift+P → Developer: Reload Window`). Make sure chat is in **Agent** mode. |
| `command not found: uv` in the VS Code terminal | Restart VS Code completely so it picks up the updated PATH. |
| Authentication errors (`401`) | Your token may be revoked. Create a new one and run **Cmd+Shift+P → MCP: Reset Server Inputs** to re-enter it. |
| `No transition named 'X' on ABC-123` | Workflows differ per project. Ask *"list transitions on ABC-123"* to see the valid names. |
| Wrong user assigned | Be more specific: full name, email, or accountId. |
| Want to start fresh | Delete `~/Documents/JIRA SUP/.venv` and run `uv sync` again. |

To re-test everything is wired up:

```bash
cd ~/Documents/"JIRA SUP"
uv run pytest          # 11 tests should pass
```

---

## 7. What to ask for next (when you're ready)

These were intentionally left out of v1 — open a follow-up to add any of them:

- Create new issues from chat
- Worklogs (time tracking)
- Watchers (add/remove)
- Sprint / board / backlog operations (Agile API)
- JSM-specific: queues, request types, SLA breach reports, customer portal actions
- Webhook-driven automation (e.g. auto-comment when status changes)
- A *team-shared* version (remote MCP server with OAuth instead of local API tokens)

---

## Quick reference: the 14 tools

**Read helpers** (Copilot calls these automatically when needed)
`get_current_user`, `list_projects`, `search_users`, `list_transitions`, `list_issue_link_types`, `list_attachments`, `get_issue`, `search_issues`

**Actions**
`add_comment`, `transition_issue`, `assign_issue`, `update_issue`, `link_issues`, `add_attachment`
