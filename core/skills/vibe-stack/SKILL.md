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
