# opencode-vibe-stack

This is a **configuration management repository** for OpenCode + OhMyOpenAgent (OMO) AI agent configurations. It does NOT contain application code.

## What You'll Find Here

- `core/` — Always-loaded resident configs (rules, skills, agents, MCP, commands)
- `domains/` — Domain-specific configs organized by category (`ai/`, `dcc/`, `game-dev/`)
- `stacks/` — Preset domain combinations (`dcc.json`, `game-dev.json`, `ai-training.json`, etc.)
- `bin/` — CLI tools (`vibe-stack`) and installers

## How Configs Are Loaded

This repo is deployed to `~/.opencode-vibe-stack/`. Symlinks connect it to the actual config paths that OMO reads:

- `~/.config/opencode/rules/` <--symlink-- `core/rules/`
- `.opencode/rules/` <--symlink-- `domains/<category>/<domain>/rules/`
- `.opencode/opencode.json` <--merge-- domain MCP configs + skill registrations

OMO's native config walking (`.opencode/` up to `$HOME`) handles the rest.

## When Working on This Repo

- Domain configs should contain ONLY rules/skills/agents/MCP content — NEVER model parameters
- Model configurations (providers, temperatures, etc.) belong in `~/.config/opencode/oh-my-openagent.jsonc` and are out of scope
- All domain directories follow the same structure: `{rules,agents,commands,mcp,skills}/`
- MCP binaries (`.exe`, binaries) are deployed to domain `mcp/` directories — committed as build artifacts
- Use `vibe-stack activate <domain>` to test domain configs in a project
- Skills are registered via `opencode.json` `skills.paths` (not OMO `skills.sources`)
