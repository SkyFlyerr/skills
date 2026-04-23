# Thread Draft: MCP Client

1. Most agent MCP setups have one hidden cost: they dump every tool schema into context before you know which tool you need.

2. I started using a smaller pattern: inspect MCP servers progressively.

3. First list servers:

```bash
python scripts/mcp_client.py servers
```

4. Then inspect one server:

```bash
python scripts/mcp_client.py tools github
```

5. Then call one tool:

```bash
python scripts/mcp_client.py call github search_repos '{"query":"python mcp"}'
```

6. The point is not the CLI. The point is the agent workflow: do not load a room full of tools when you only need one drawer.

7. It supports local stdio servers, SSE, streamable HTTP, and FastMCP-style Bearer auth.

8. The config can stay in `.mcp.json`, `MCP_CONFIG_PATH`, or inline `MCP_CONFIG`.

9. It is deliberately boring: JSON in, JSON out, small script, easy to inspect.

10. First public skill in the collection: `mcp-client`.

Repo: https://github.com/SkyFlyerr/skills
