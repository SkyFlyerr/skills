# MCP Client

A tiny command-line bridge for Model Context Protocol servers.

Agents often lose a lot of context budget when every MCP tool schema is loaded
upfront. This skill keeps MCP usage progressive: list configured servers, inspect
one server's tools, then call exactly the tool you need.

## What You Get

- A single Python CLI: `scripts/mcp_client.py`
- Support for `stdio`, `sse`, streamable HTTP, and FastMCP-style Bearer auth
- JSON output designed for agents and shell pipelines
- Config via `MCP_CONFIG_PATH`, inline `MCP_CONFIG`, local `.mcp.json`, or user config

## Quickstart

```bash
cd skills/mcp-client
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp examples/mcp-config.example.json .mcp.json
python scripts/mcp_client.py servers
```

Expected output:

```json
[
  {
    "name": "sequential-thinking",
    "transport": "stdio",
    "command": "npx"
  },
  {
    "name": "zapier",
    "transport": "fastmcp",
    "url": "https://mcp.zapier.com/api/v1/connect"
  }
]
```

## Commands

```bash
python scripts/mcp_client.py servers
python scripts/mcp_client.py tools <server>
python scripts/mcp_client.py call <server> <tool> '{"arg":"value"}'
```

## Config

The CLI accepts both standard MCP config shape and a direct server map:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"]
    }
  }
}
```

For remote authenticated servers, prefer environment variables:

```json
{
  "mcpServers": {
    "zapier": {
      "url": "https://mcp.zapier.com/api/v1/connect",
      "api_key_env": "ZAPIER_MCP_API_KEY"
    }
  }
}
```

## Demo

Run a dependency-free smoke demo with inline config:

```bash
MCP_CONFIG='{"mcpServers":{"demo":{"command":"python3","args":["--version"]}}}' python scripts/mcp_client.py servers
```

That confirms config parsing and transport detection. To actually call tools,
configure a real MCP server such as Sequential Thinking, Filesystem, GitHub, or
Zapier.

## When Not To Use

- You already have the needed MCP tool directly exposed to the agent.
- The task needs continuous interactive sessions rather than one-shot inspection
  and calls.
- The server exposes high-risk write actions and you do not have explicit user
  permission to call them.

## Failure Modes

- `configuration`: no config found or invalid JSON.
- `validation`: missing server/tool or invalid arguments.
- `connection`: server could not be reached or initialized.
- `error`: unexpected runtime error from the server or dependency stack.

All errors are printed as JSON so an agent can handle them without parsing
tracebacks.
