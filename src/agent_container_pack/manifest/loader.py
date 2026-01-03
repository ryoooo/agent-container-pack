"""Load and parse agentpack.yml manifest files."""

from pathlib import Path

import yaml

from agent_container_pack.manifest.schema import Manifest


class ManifestError(Exception):
    """Base exception for manifest errors."""


class ManifestNotFoundError(ManifestError):
    """Manifest file not found."""


class ManifestParseError(ManifestError):
    """Failed to parse manifest file."""


def load_manifest(path: Path | str) -> Manifest:
    """Load manifest from YAML file or directory.

    Args:
        path: Path to agentpack.yml or directory containing it.

    Returns:
        Validated Manifest object.

    Raises:
        ManifestNotFoundError: If manifest file not found.
        ManifestParseError: If manifest is invalid.
    """
    path = Path(path)

    if path.is_dir():
        path = path / "agentpack.yml"

    if not path.exists():
        raise ManifestNotFoundError(f"Manifest not found: {path}")

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ManifestParseError(f"Failed to parse YAML: {e}") from e

    try:
        return Manifest.model_validate(data)
    except Exception as e:
        raise ManifestParseError(f"Invalid manifest: {e}") from e
