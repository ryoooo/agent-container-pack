"""Update init-firewall.sh with MCP server domains."""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from agent_container_pack.manifest.schema import Manifest, MCPServerHTTP


@dataclass
class FirewallUpdateResult:
    """Result of firewall update operation."""

    success: bool
    message: str
    domains_added: int = 0


def extract_domains(manifest: Manifest) -> set[str]:
    """Extract domains from HTTP MCP servers.

    Args:
        manifest: Validated manifest.

    Returns:
        Set of domain names.
    """
    domains: set[str] = set()

    for server in manifest.mcp.servers.values():
        if isinstance(server, MCPServerHTTP):
            parsed = urlparse(server.url)
            if parsed.hostname:
                domains.add(parsed.hostname)

    return domains


def update_firewall(manifest: Manifest, project_dir: Path) -> FirewallUpdateResult:
    """Update init-firewall.sh with MCP server domains.

    Args:
        manifest: Validated manifest.
        project_dir: Project directory.

    Returns:
        Result of update operation.
    """
    domains = extract_domains(manifest)
    if not domains:
        return FirewallUpdateResult(
            success=True,
            message="No HTTP MCP servers to add",
            domains_added=0,
        )

    firewall_script = project_dir / ".devcontainer" / "init-firewall.sh"
    if not firewall_script.exists():
        return FirewallUpdateResult(
            success=False,
            message=f"Firewall script not found: {firewall_script}",
        )

    content = firewall_script.read_text()

    # Find ALLOWED_DOMAINS array
    pattern = r"(ALLOWED_DOMAINS=\(\s*\n)(.*?)(\))"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return FirewallUpdateResult(
            success=False,
            message="Could not find ALLOWED_DOMAINS array in firewall script",
        )

    # Get existing domains
    existing_block = match.group(2)
    existing_domains = set(re.findall(r'"([^"]+)"', existing_block))

    # Add new domains
    new_domains = domains - existing_domains
    if not new_domains:
        return FirewallUpdateResult(
            success=True,
            message="All domains already present",
            domains_added=0,
        )

    # Build new array content
    all_domains = sorted(existing_domains | new_domains)
    new_block = "\n".join(f'    "{domain}"' for domain in all_domains)

    new_content = content[: match.start(2)] + new_block + content[match.end(2) :]
    firewall_script.write_text(new_content)

    return FirewallUpdateResult(
        success=True,
        message=f"Added domains: {sorted(new_domains)}",
        domains_added=len(new_domains),
    )
