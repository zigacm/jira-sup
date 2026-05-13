---
name: jira-agent-connect
description: 'Connect to Jira server and switch to Agent mode. Use when you want to start working with Jira tickets, search issues, or manage projects in a single step.'
argument-hint: 'Optional issue key (e.g., CGG-256) to jump directly to after connecting'
user-invocable: true
---

# Jira Agent Connect

One-command Jira server startup + Agent mode switch.

## When to Use
- Starting a Jira PM session
- Jumping into ticket triage or management
- Running bulk operations on issues
- Quick ticket lookups

## What Happens
1. Checks if MCP server is running (starts if needed)
2. Instructs you to switch to **Agent** mode in Copilot Chat
3. Ready for natural language Jira commands

## Quick Start

1. **Run this skill** (`/jira-agent-connect`)
2. **Switch mode**: Copilot Chat dropdown → **Agent**
3. **Talk to it**: 
   - "show me my open tickets"
   - "get CGG-256"
   - "close SUP-142 with comment 'Fixed'"

## Server Health Check

Run [check-server.sh](./scripts/check-server.sh) if you suspect the server crashed.

## Common Commands

- `search CGG project for unresolved tickets`
- `assign SUP-123 to me`
- `what's the status of CGG-256?`
- `link CGG-100 as blocked by CGG-99`

See the [GUIDE.md](../../GUIDE.md) for full command reference.
