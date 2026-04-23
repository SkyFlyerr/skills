---
name: mcp-client
description: Use a lightweight CLI to inspect and call MCP servers on demand, keeping large MCP tool schemas out of the agent context until they are needed.
---

# MCP Client Skill

Use this skill when a task needs an MCP server but loading every available tool
schema into the main agent context would be noisy or expensive.

## When To Use

- The user asks to connect to, inspect, or call an MCP server.
- You need to list available MCP tools before deciding which one to call.
- You have a local or remote MCP config and want a narrow command-line bridge.
- You want progressive disclosure: first servers, then tools, then one tool call.

## When Not To Use

- The MCP tool is already exposed directly in the current environment.
- The task needs long-lived bidirectional interaction that is better handled by
  a dedicated app or native MCP integration.
- You do not have permission to access the configured server or its data.

## Setup

```bash
cd skills/mcp-client
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp examples/mcp-config.example.json .mcp.json
```

Edit `.mcp.json` with the servers the user has authorized.

## Workflow

1. List configured servers:

```bash
python scripts/mcp_client.py servers
```

2. Inspect tools for one server:

```bash
python scripts/mcp_client.py tools sequential-thinking
```

3. Call one tool with JSON arguments:

```bash
python scripts/mcp_client.py call sequential-thinking sequentialthinking '{"thought":"Break down the task","thoughtNumber":1,"totalThoughts":3,"nextThoughtNeeded":true}'
```

## Config Sources

The CLI checks config in this order:

1. `MCP_CONFIG_PATH`
2. `MCP_CONFIG` inline JSON
3. `.mcp.json` in the current directory
4. `~/.config/mcp-client/config.json`

Prefer `api_key_env` over hardcoded `api_key` for public or shared configs.

## Safety Rules

- Never commit real MCP API keys or service tokens.
- Use the narrowest filesystem paths and API scopes possible.
- Inspect tools before calling them when the server exposes mutating actions.
- Report JSON errors directly instead of guessing whether a call succeeded.
