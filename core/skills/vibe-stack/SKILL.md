# Vibe Stack - Domain Configuration Manager

Manage domain-specific configurations for AI agent toolchains.

## Overview

Vibe Stack provides a layered configuration system for OpenCode + OhMyOpenAgent (OMO).
It isolates rules, agents, MCPs, commands, and skills per domain (e.g., Unity, Unreal, Blender).

Domain configs are stored in a central git repository and activated per project via symlinks.

## Key Locations

| Path | Purpose |
|------|---------|
| `~/.opencode-vibe-stack/core/` | Always-loaded resident configs |
| `~/.opencode-vibe-stack/domains/<category>/<domain>/` | Domain-specific configs |
| `~/.opencode-vibe-stack/stacks/` | Preset domain combinations |
| `~/.config/opencode/` | User-level config (symlinks to core/) |
| `.opencode/` | Project-level config (symlinks to domains/) |

## Usage Commands

When you need to manage domain configs, use the `vibe-stack` CLI:

```bash
# List all available domains
vibe-stack list

# Show active domains in current project
vibe-stack status

# Activate a domain for the current project
vibe-stack activate game-dev/unity

# Deactivate a domain
vibe-stack deactivate game-dev/unity

# Activate a preset stack
vibe-stack use-stack game-dev
```

## Adding New Domains

1. Create directory: `domains/<category>/<domain>/`
2. Add required subdirectories: `rules/`, `agents/`, `commands/`, `mcp/`, `skills/`
3. Configure domain-specific rules, agents, etc.
4. Commit and push to the repository

## Configuration Layering

When a project is opened, configs are loaded in this order:
1. **Core** (always loaded) - from `~/.config/opencode/` (symlinked to core/)
2. **Project** - from `.opencode/` in the project root
3. **Domain** - from symlinks created by `vibe-stack activate`

OMO's native config walking (`.opencode/` up to `$HOME`) handles merging automatically.

## MCP Server Management

Domain MCP servers are loaded **only when the domain is activated** — no global MCP clutter.

### How It Works

1. Each domain's `mcp/` directory contains one or more JSON definition files in OpenCode native format
2. On `vibe-stack activate`, the CLI:
   - Reads all `mcp/*.json` files from the domain
   - Resolves `${VIBE_STACK_HOME}` and `${PROJECT_ROOT}` placeholders
   - Adds `vibe:` namespace prefix to server names (e.g., `vibe:data-forge`)
   - Merges entries into `.opencode/opencode.json` under the `mcp` key
3. OpenCode auto-discovers `.opencode/opencode.json` on startup and connects to the MCP servers
4. On `vibe-stack deactivate`, the `vibe:*` entries are removed

### MCP Definition Format

Use OpenCode native `mcp` format in domain definition files:

```json
{
  "mcp": {
    "server-name": {
      "type": "local",
      "command": ["python", "${VIBE_STACK_HOME}/domains/my-cat/my-domain/mcp/my-server/server.py"],
      "enabled": true,
      "environment": {
        "MY_VAR": "${PROJECT_ROOT}/data"
      }
    }
  }
}
```

### Directory Structure

```
domains/<category>/<domain>/
  mcp/
    my-server.json       # MCP definition (OpenCode format)
    my-server/           # MCP server project code (optional)
      pyproject.toml
      src/server.py
```

### Key Rules

- **No user config modified** — all MCP config writes to `.opencode/opencode.json` (project-level)
- **Namespace isolation** — `vibe:` prefix prevents collision with user/Claude Code MCPs
- **Placeholder resolution** — `${VIBE_STACK_HOME}` and `${PROJECT_ROOT}` resolved at activation time
- **Per-domain lifecycle** — MCPs activate/deactivate with their domain
