"""Generate CLAUDE.md / AGENTS.md from manifest."""

from agentpack.manifest.schema import Manifest, SafetyConfig

SAFETY_PRESET_DEFAULT = [
    "secrets禁止（API_KEY等を直書きしない）",
    "破壊操作は段階的に: dry-run → diff → apply",
]


def _generate_safety_section(safety: SafetyConfig) -> str:
    """Generate safety section."""
    lines: list[str] = []

    if safety.preset == "default":
        for rule in SAFETY_PRESET_DEFAULT:
            lines.append(f"- {rule}")

    for rule in safety.custom:
        lines.append(f"- {rule}")

    if not lines:
        return ""

    return "## Safety\n\n" + "\n".join(lines) + "\n"


def generate_claude_md(manifest: Manifest) -> str:
    """Generate CLAUDE.md content from manifest.

    Args:
        manifest: Validated manifest object.

    Returns:
        Generated markdown content.
    """
    sections: list[str] = []

    # Header
    sections.append(f"# {manifest.project.name}\n")
    sections.append(f"{manifest.project.description}\n")

    # Commands section (if stack is specified)
    stack_config = None
    if manifest.stack and manifest.stack in manifest.stacks:
        stack_config = manifest.stacks[manifest.stack]
    elif manifest.stacks:
        # Use first available stack
        stack_config = next(iter(manifest.stacks.values()))

    if stack_config:
        commands: list[str] = []
        if stack_config.deps:
            commands.append(f"- **deps**: `{stack_config.deps}`")
        if stack_config.lint:
            commands.append(f"- **lint**: `{stack_config.lint}`")
        if stack_config.typecheck:
            commands.append(f"- **typecheck**: `{stack_config.typecheck}`")
        if stack_config.test:
            commands.append(f"- **test**: `{stack_config.test}`")
        if stack_config.run:
            commands.append(f"- **run**: `{stack_config.run}`")

        if commands:
            sections.append("## Commands\n")
            sections.append("\n".join(commands) + "\n")

    # Workflows section
    if manifest.workflows:
        sections.append("## Workflows\n")
        for workflow in manifest.workflows:
            sections.append(f"### {workflow.name}\n")
            for i, step in enumerate(workflow.steps, 1):
                sections.append(f"{i}. `{step}`")
            sections.append("")

    # Pre-commit section
    if manifest.pre_commit:
        sections.append("## Pre-commit\n")
        for tool in manifest.pre_commit:
            sections.append(f"- {tool}")
        sections.append("")

    # Safety section
    safety_section = _generate_safety_section(manifest.safety)
    if safety_section:
        sections.append(safety_section)

    # Custom content
    if manifest.custom_content:
        sections.append(manifest.custom_content.rstrip() + "\n")

    return "\n".join(sections)
