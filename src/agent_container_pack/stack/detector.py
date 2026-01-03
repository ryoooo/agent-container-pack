"""Detect stack from project files."""

from pathlib import Path

from agent_container_pack.manifest.schema import Manifest


class StackError(Exception):
    """Base exception for stack errors."""


class NoStackDetectedError(StackError):
    """No stack could be detected."""


class AmbiguousStackError(StackError):
    """Multiple stacks detected, ambiguous selection."""


def detect_stack(
    manifest: Manifest,
    project_dir: Path,
    *,
    use_manifest_stack: bool = False,
) -> str:
    """Detect stack from project files.

    Args:
        manifest: Validated manifest with stack definitions.
        project_dir: Project directory to scan.
        use_manifest_stack: If True and manifest.stack is set, use it directly.

    Returns:
        Detected stack ID.

    Raises:
        NoStackDetectedError: If no stack files found.
        AmbiguousStackError: If multiple stacks detected in single-stack mode.
    """
    # Use explicit stack if specified
    if use_manifest_stack and manifest.stack:
        return manifest.stack

    detected: list[str] = []

    for stack_id, stack_config in manifest.stacks.items():
        for pattern in stack_config.detect.any:
            if (project_dir / pattern).exists():
                detected.append(stack_id)
                break

    if not detected:
        raise NoStackDetectedError(
            f"No stack detected in {project_dir}. "
            f"Expected one of: {list(manifest.stacks.keys())}"
        )

    if len(detected) > 1 and manifest.docs.mode == "single-stack":
        raise AmbiguousStackError(
            f"Multiple stacks detected: {detected}. "
            f"Use --stack to specify one, or set docs.mode to multi-stack."
        )

    return detected[0]
