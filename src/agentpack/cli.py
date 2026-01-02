"""Agentpack CLI."""

import cyclopts

app = cyclopts.App(
    name="agentpack",
    help="Generate CLAUDE.md/AGENTS.md from agentpack.yml",
)


@app.default
def main() -> None:
    """Show help by default."""
    print(app.help_format())


if __name__ == "__main__":
    app()
