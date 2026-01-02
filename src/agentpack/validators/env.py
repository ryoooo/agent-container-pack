"""Validate environment variable references."""

import re
from dataclasses import dataclass
from pathlib import Path

from agentpack.manifest.schema import Manifest

# Match ${VAR} or ${env:VAR}
ENV_REF_PATTERN = re.compile(r"\$\{(?:env:)?([A-Z_][A-Z0-9_]*)\}")


@dataclass
class EnvValidationWarning:
    """Warning about environment variable issues."""

    message: str


def _extract_env_refs(manifest: Manifest) -> set[str]:
    """Extract all environment variable references from manifest.

    Args:
        manifest: Validated manifest.

    Returns:
        Set of referenced variable names.
    """
    refs: set[str] = set()

    for server in manifest.mcp.servers.values():
        for value in server.env.values():
            matches = ENV_REF_PATTERN.findall(value)
            refs.update(matches)

    return refs


def _parse_env_file(path: Path) -> set[str]:
    """Parse .env file and return defined variable names.

    Args:
        path: Path to .env file.

    Returns:
        Set of defined variable names.
    """
    if not path.exists():
        return set()

    defined: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key = line.split("=", 1)[0].strip()
            if key:
                defined.add(key)

    return defined


def validate_env_vars(manifest: Manifest, project_dir: Path) -> list[EnvValidationWarning]:
    """Validate environment variable references.

    Args:
        manifest: Validated manifest.
        project_dir: Project directory.

    Returns:
        List of warnings for missing variables.
    """
    warnings: list[EnvValidationWarning] = []

    refs = _extract_env_refs(manifest)
    if not refs:
        return warnings

    env_file = project_dir / ".devcontainer" / ".env"
    defined = _parse_env_file(env_file)

    for ref in sorted(refs):
        if ref not in defined:
            warnings.append(
                EnvValidationWarning(
                    f"Environment variable {ref} is referenced but not defined in "
                    f".devcontainer/.env"
                )
            )

    return warnings
