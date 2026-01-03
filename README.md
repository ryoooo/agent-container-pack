# agentpack

CLI tool that generates CLAUDE.md/AGENTS.md and MCP configurations from a single `agentpack.yml` manifest.

## Why agentpack?

Claude Code and Codex CLI have different configuration formats. agentpack uses a single YAML manifest as the source of truth, generating the appropriate files for each tool:

- `CLAUDE.md` / `AGENTS.md` - Project instructions
- `.claude/settings.json` - Claude Code MCP configuration
- `codex.config.toml` - Codex CLI MCP configuration

## Quick Start

```bash
# Install
uv add agentpack

# Initialize a new project
agentpack init --stack python

# Generate configuration files
agentpack generate --write
```

## Commands

### `agentpack init`

Initialize a new agentpack project with devcontainer and manifest skeleton.

```bash
agentpack init [directory] [--template <source>] [--stack <id>] [--force]
```

| Option | Description | Default |
|--------|-------------|---------|
| `directory` | Target directory | `.` |
| `--template` | Template source | `github:agentpack/template-default` |
| `--stack` | Stack to use (python, node, etc.) | - |
| `--force` | Overwrite existing files | `false` |

### `agentpack generate`

Generate configuration files from `agentpack.yml`.

```bash
agentpack generate [--write] [--directory <path>]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--write` | Write files to disk (otherwise dry-run) | `false` |
| `--directory` | Project directory | `.` |

## Manifest Format

Create an `agentpack.yml` in your project root:

```yaml
version: "1"

project:
  name: "my-project"
  description: "Project description"

stack: python

stacks:
  python:
    detect:
      any: ["pyproject.toml", "requirements.txt"]
    deps: "uv sync"
    lint: "uv run ruff check ."
    typecheck: "uv run ty check"
    test: "uv run pytest"
    run: "uv run python main.py"

mcp:
  servers:
    memory:
      transport: stdio
      command: ["npx", "@anthropic/mcp-memory"]
      env:
        MEMORY_PATH: "${workspaceFolder}/.memory"

workflows:
  - name: "Development Flow"
    steps:
      - "uv run ruff format . && uv run ruff check ."
      - "uv run pytest"

pre_commit: ["prettier", "ruff", "ty"]

safety:
  preset: default
```

See [docs/plans/2026-01-02-agentpack-v0.1-design.md](docs/plans/2026-01-02-agentpack-v0.1-design.md) for full manifest specification.

## Generated Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Claude Code project instructions |
| `AGENTS.md` | Codex CLI project instructions (same content) |
| `.claude/settings.json` | Claude Code MCP server configuration |
| `codex.config.toml` | Codex CLI MCP server configuration |

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff format .
uv run ruff check .

# Type check
uv run ty check
```

## License

MIT
