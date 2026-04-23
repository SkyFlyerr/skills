# MCP Client Demo Commands

```bash
cd skills/mcp-client
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp examples/mcp-config.example.json .mcp.json
python scripts/mcp_client.py servers
python scripts/mcp_client.py tools sequential-thinking
```

For a smoke test that does not require dependencies or network:

```bash
MCP_CONFIG='{"mcpServers":{"demo":{"command":"python3","args":["--version"]}}}' python scripts/mcp_client.py servers
```
