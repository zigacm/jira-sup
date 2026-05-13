#!/bin/bash
# Check if MCP Jira server is running; start if needed

cd /Users/ziga/Documents/JIRA\ SUP || exit 1

# Check for existing process
if pgrep -f "python -m jira_mcp" > /dev/null; then
    echo "✅ MCP server is running"
    exit 0
fi

echo "🚀 Starting MCP server..."
nohup uv run python -m jira_mcp > /tmp/jira_mcp.log 2>&1 &

sleep 2
if pgrep -f "python -m jira_mcp" > /dev/null; then
    echo "✅ MCP server started successfully"
    echo "📝 Logs: tail -f /tmp/jira_mcp.log"
    exit 0
else
    echo "❌ Failed to start server. Check: cat /tmp/jira_mcp.log"
    exit 1
fi
