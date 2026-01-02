"""Generate .claude/settings.json from manifest."""

import json
from typing import Any

from agentpack.manifest.schema import Manifest, MCPServerStdio


def generate_settings_json(manifest: Manifest) -> str:
    """Generate .claude/settings.json content from manifest.

    Args:
        manifest: Validated manifest object.

    Returns:
        Generated JSON content.
    """
    mcp_servers: dict[str, Any] = {}

    for name, server in manifest.mcp.servers.items():
        if isinstance(server, MCPServerStdio):
            server_config: dict[str, Any] = {
                "command": server.command[0],
                "args": server.command[1:],
            }
            if server.env:
                server_config["env"] = server.env
            if server.cwd:
                server_config["cwd"] = server.cwd
        else:
            # HTTP server - skip for Claude settings (not supported)
            continue

        mcp_servers[name] = server_config

    settings: dict[str, Any] = {}
    if mcp_servers:
        settings["mcpServers"] = mcp_servers

    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
