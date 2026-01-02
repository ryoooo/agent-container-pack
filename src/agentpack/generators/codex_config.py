"""Generate codex.config.toml from manifest."""

from agentpack.manifest.schema import Manifest, MCPServerHTTP, MCPServerStdio


def _format_toml_value(value: str | list[str] | dict[str, str]) -> str:
    """Format a value for TOML output."""
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, list):
        items = ", ".join(f'"{item}"' for item in value)
        return f"[{items}]"
    elif isinstance(value, dict):
        items = ", ".join(f'"{k}" = "{v}"' for k, v in value.items())
        return f"{{ {items} }}"
    return str(value)


def generate_codex_config(manifest: Manifest) -> str:
    """Generate codex.config.toml content from manifest.

    Args:
        manifest: Validated manifest object.

    Returns:
        Generated TOML content.
    """
    lines: list[str] = []

    for name, server in manifest.mcp.servers.items():
        lines.append(f"[mcp_servers.{name}]")

        if isinstance(server, MCPServerStdio):
            lines.append(f'command = "{server.command[0]}"')
            if len(server.command) > 1:
                lines.append(f"args = {_format_toml_value(server.command[1:])}")
            if server.env:
                lines.append(f"env = {_format_toml_value(server.env)}")
            if server.cwd:
                lines.append(f'cwd = "{server.cwd}"')
        elif isinstance(server, MCPServerHTTP):
            lines.append(f'url = "{server.url}"')

        lines.append("")

    return "\n".join(lines)
