"""Generate codex.config.toml from manifest."""

from agentpack.manifest.schema import Manifest, MCPServerHTTP, MCPServerStdio


def _escape_toml_string(value: str) -> str:
    """Escape a string for TOML output."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _format_toml_value(value: str | list[str] | dict[str, str]) -> str:
    """Format a value for TOML output."""
    if isinstance(value, str):
        return f'"{_escape_toml_string(value)}"'
    elif isinstance(value, list):
        items = ", ".join(f'"{_escape_toml_string(item)}"' for item in value)
        return f"[{items}]"
    elif isinstance(value, dict):
        items = ", ".join(
            f'"{_escape_toml_string(k)}" = "{_escape_toml_string(v)}"'
            for k, v in value.items()
        )
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
            lines.append(f'command = "{_escape_toml_string(server.command[0])}"')
            if len(server.command) > 1:
                lines.append(f"args = {_format_toml_value(server.command[1:])}")
            if server.env:
                lines.append(f"env = {_format_toml_value(server.env)}")
            if server.cwd:
                lines.append(f'cwd = "{_escape_toml_string(server.cwd)}"')
        elif isinstance(server, MCPServerHTTP):
            lines.append(f'url = "{_escape_toml_string(server.url)}"')

        lines.append("")

    return "\n".join(lines)
