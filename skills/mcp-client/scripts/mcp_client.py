#!/usr/bin/env python3
"""
Small MCP client for progressive disclosure.

Usage:
    python scripts/mcp_client.py servers
    python scripts/mcp_client.py tools <server>
    python scripts/mcp_client.py call <server> <tool> '{"arg": "value"}'

Config sources:
    1. MCP_CONFIG_PATH: path to a JSON config file
    2. MCP_CONFIG: inline JSON
    3. .mcp.json in the current directory
    4. ~/.config/mcp-client/config.json
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional


USER_CONFIG_PATH = Path.home() / ".config" / "mcp-client" / "config.json"


def normalize_config(raw_config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Accept either standard MCP config shape or a direct server map."""
    servers = raw_config.get("mcpServers", raw_config)
    if not isinstance(servers, dict):
        raise ValueError("MCP config must contain an object of server definitions.")
    return servers


def find_config_file() -> Optional[Path]:
    if env_path := os.environ.get("MCP_CONFIG_PATH"):
        path = Path(env_path).expanduser()
        if path.exists():
            return path
        raise FileNotFoundError(f"MCP_CONFIG_PATH does not exist: {path}")

    local_config = Path(".mcp.json")
    if local_config.exists():
        return local_config

    if USER_CONFIG_PATH.exists():
        return USER_CONFIG_PATH

    return None


def load_config() -> dict[str, dict[str, Any]]:
    if env_config := os.environ.get("MCP_CONFIG"):
        try:
            return normalize_config(json.loads(env_config))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid MCP_CONFIG JSON: {exc}") from exc

    config_path = find_config_file()
    if not config_path:
        raise FileNotFoundError(
            "No MCP config found. Set MCP_CONFIG_PATH, set MCP_CONFIG, "
            "create .mcp.json, or create ~/.config/mcp-client/config.json."
        )

    try:
        with config_path.open() as config_file:
            return normalize_config(json.load(config_file))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {config_path}: {exc}") from exc


def get_server_config(servers: dict[str, dict[str, Any]], server_name: str) -> dict[str, Any]:
    if server_name not in servers:
        available = ", ".join(sorted(servers)) or "none"
        raise ValueError(f"Server '{server_name}' not found. Available: {available}")
    config = servers[server_name]
    if not isinstance(config, dict):
        raise ValueError(f"Server '{server_name}' config must be an object.")
    return config


def resolve_api_key(config: dict[str, Any]) -> Optional[str]:
    if api_key := config.get("api_key"):
        return str(api_key)

    if api_key_env := config.get("api_key_env"):
        value = os.environ.get(str(api_key_env))
        if not value:
            raise ValueError(f"Environment variable {api_key_env} is required.")
        return value

    return None


def resolve_headers(config: dict[str, Any]) -> Optional[dict[str, str]]:
    headers = config.get("headers")
    if headers is not None and not isinstance(headers, dict):
        raise ValueError("headers must be an object when provided.")

    resolved_headers = {str(key): str(value) for key, value in (headers or {}).items()}
    if api_key := resolve_api_key(config):
        resolved_headers.setdefault("Authorization", f"Bearer {api_key}")

    return resolved_headers or None


def detect_transport(config: dict[str, Any]) -> str:
    if explicit_type := config.get("type"):
        type_map = {
            "stdio": "stdio",
            "sse": "sse",
            "http": "streamable_http",
            "streamable_http": "streamable_http",
            "streamable-http": "streamable_http",
            "fastmcp": "fastmcp",
        }
        return type_map.get(str(explicit_type).lower(), str(explicit_type).lower())

    if "command" in config:
        return "stdio"

    if "url" in config:
        if "api_key" in config or "api_key_env" in config:
            return "fastmcp"

        url = str(config["url"])
        if url.endswith("/mcp"):
            return "streamable_http"
        if url.endswith("/sse"):
            return "sse"
        return "sse"

    raise ValueError("Cannot detect transport: server config must have 'command' or 'url'.")


@asynccontextmanager
async def create_session(config: dict[str, Any]):
    transport = detect_transport(config)

    if transport == "stdio":
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        env = {**os.environ}
        if config_env := config.get("env"):
            if not isinstance(config_env, dict):
                raise ValueError("env must be an object when provided.")
            env.update({str(key): str(value) for key, value in config_env.items()})

        server_params = StdioServerParameters(
            command=str(config["command"]),
            args=[str(arg) for arg in config.get("args", [])],
            env=env,
            cwd=config.get("cwd"),
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    elif transport == "sse":
        from mcp import ClientSession
        from mcp.client.sse import sse_client

        async with sse_client(
            str(config["url"]),
            headers=resolve_headers(config),
            timeout=float(config.get("timeout", 30)),
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    elif transport == "streamable_http":
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(
            str(config["url"]),
            headers=resolve_headers(config),
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    elif transport == "fastmcp":
        from fastmcp import Client
        from fastmcp.client.transports import StreamableHttpTransport

        headers = resolve_headers(config)
        client = Client(transport=StreamableHttpTransport(str(config["url"]), headers=headers))

        async with client:
            yield FastMCPSessionAdapter(client)

    else:
        raise ValueError(f"Unsupported transport: {transport}")


class FastMCPSessionAdapter:
    """Expose FastMCP Client with the subset of ClientSession used by this CLI."""

    def __init__(self, client: Any):
        self.client = client

    async def list_tools(self) -> Any:
        tools = await self.client.list_tools()
        return type("ToolsResult", (), {"tools": tools})()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        return await self.client.call_tool(name, arguments)


def cmd_servers(servers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for name, config in sorted(servers.items()):
        transport = detect_transport(config)
        item: dict[str, Any] = {
            "name": name,
            "transport": transport,
        }
        if transport == "stdio":
            item["command"] = config.get("command")
        else:
            item["url"] = config.get("url")
        result.append(item)
    return result


async def cmd_tools(servers: dict[str, dict[str, Any]], server_name: str) -> list[dict[str, Any]]:
    config = get_server_config(servers, server_name)
    async with create_session(config) as session:
        result = await session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            }
            for tool in result.tools
        ]


async def cmd_call(
    servers: dict[str, dict[str, Any]],
    server_name: str,
    tool_name: str,
    arguments: dict[str, Any],
) -> Any:
    config = get_server_config(servers, server_name)
    async with create_session(config) as session:
        result = await session.call_tool(tool_name, arguments)

    if hasattr(result, "content"):
        contents = []
        for item in result.content:
            if hasattr(item, "text"):
                contents.append(item.text)
            elif hasattr(item, "data"):
                contents.append({"type": "data", "data": item.data})
            else:
                contents.append(str(item))
        return contents[0] if len(contents) == 1 else contents

    return result


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def print_error(message: str, error_type: str = "error") -> None:
    print_json({"error": message, "type": error_type})


def print_usage() -> None:
    print(
        """Usage: mcp_client.py <command> [args]

Commands:
    servers                           List configured MCP servers
    tools <server>                    List tools with full schemas
    call <server> <tool> '<json>'     Execute a tool with arguments

Examples:
    python scripts/mcp_client.py servers
    python scripts/mcp_client.py tools github
    python scripts/mcp_client.py call github search_repos '{"query": "python mcp"}'

Config sources:
    1. MCP_CONFIG_PATH
    2. MCP_CONFIG
    3. .mcp.json
    4. ~/.config/mcp-client/config.json"""
    )


async def main() -> None:
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command in {"--help", "-h", "help"}:
        print_usage()
        return

    try:
        servers = load_config()

        if command == "servers":
            print_json(cmd_servers(servers))
            return

        if command == "tools":
            if len(sys.argv) < 3:
                print_error("Usage: tools <server_name>", "usage")
                sys.exit(1)
            print_json(await cmd_tools(servers, sys.argv[2]))
            return

        if command == "call":
            if len(sys.argv) < 4:
                print_error("Usage: call <server> <tool> [json_args]", "usage")
                sys.exit(1)

            args: dict[str, Any] = {}
            if len(sys.argv) >= 5:
                try:
                    parsed_args = json.loads(sys.argv[4])
                except json.JSONDecodeError as exc:
                    print_error(f"Invalid JSON arguments: {exc}", "invalid_args")
                    sys.exit(1)
                if not isinstance(parsed_args, dict):
                    print_error("Tool arguments must be a JSON object.", "invalid_args")
                    sys.exit(1)
                args = parsed_args

            print_json(await cmd_call(servers, sys.argv[2], sys.argv[3], args))
            return

        print_error(f"Unknown command: {command}", "usage")
        print_usage()
        sys.exit(1)

    except FileNotFoundError as exc:
        print_error(str(exc), "configuration")
        sys.exit(1)
    except ValueError as exc:
        print_error(str(exc), "validation")
        sys.exit(1)
    except ConnectionError as exc:
        print_error(f"Connection failed: {exc}", "connection")
        sys.exit(1)
    except Exception as exc:
        print_error(f"Error: {exc}", "error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
