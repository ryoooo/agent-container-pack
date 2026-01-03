# agent-container-pack (acp)

CLI tool that generates CLAUDE.md/AGENTS.md and MCP configurations from a single `agentpack.yml` manifest.

## Why acp?

Claude Code and Codex CLI have different configuration formats. acp uses a single YAML manifest (`agentpack.yml`) as the source of truth, generating the appropriate files for each tool:

- `CLAUDE.md` / `AGENTS.md` - Project instructions
- `.claude/settings.json` - Claude Code MCP configuration
- `codex.config.toml` - Codex CLI MCP configuration

## Installation

```bash
# With uv (recommended)
uvx acp --help

# Or install globally
uv tool install agent-container-pack

# Or with pip
pip install agent-container-pack
```

## Usage

### New Project

```bash
# 1. Initialize project (creates .devcontainer/ and agentpack.yml)
cd my-project
acp init

# 2. Edit agentpack.yml (project name, MCP servers, etc.)
vim agentpack.yml

# 3. Generate configuration files
acp generate --write
```

### Existing Project

```bash
# 1. Create agentpack.yml manually or via init
acp init

# 2. Edit agentpack.yml to match your project
vim agentpack.yml

# 3. Generate
acp generate --write
```

### Team Workflow

```bash
# Team members clone the repo and run:
git clone <repo>
cd <repo>
acp generate --write
# → Ready to use Claude Code / Codex CLI
```

### Workflow Diagram

```
acp init          # Run once
       ↓
agentpack.yml           # Edit this file (single source of truth)
       ↓
acp generate      # Run after each yml change
       ↓
CLAUDE.md, AGENTS.md    # Auto-generated (don't edit manually)
.claude/settings.json
codex.config.toml
```

## Commands

### `acp init`

Initialize a new agentpack project with devcontainer and manifest skeleton.

```bash
acp init [directory] [--template <source>] [--stack <id>] [--force]
```

| Option | Description | Default |
|--------|-------------|---------|
| `directory` | Target directory | `.` |
| `--template` | Template source | `github:ryoooo/acp-template-default` |
| `--stack` | Stack to use (python, node, etc.) | `python` |
| `--force` | Overwrite existing files | `false` |

### `acp generate`

Generate configuration files from `agentpack.yml`.

```bash
acp generate [--write] [--directory <path>]
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
    Ref:
      transport: http
      url: "https://api.ref.tools/mcp"
      env:
        X_REF_API_KEY: "${env:X_REF_API_KEY}"

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
