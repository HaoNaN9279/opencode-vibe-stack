# opencode-vibe-stack

This is a **configuration management repository** for OpenCode + OhMyOpenAgent (OMO) AI agent configurations. It does NOT contain application code.

## What You'll Find Here

- `core/` — Always-loaded resident configs (rules, skills, agents)
- `domains/` — Domain-specific configs organized by category
- `stacks/` — Preset domain combinations
- `bin/` — CLI management tools
- `install.sh` / `install.ps1` — One-click deployment

## How Configs Are Loaded

This repo is deployed to `~/.opencode-vibe-stack/`. Symlinks connect it to the actual config paths that OMO reads:

- `~/.config/opencode/rules/` <--symlink-- `core/rules/`
- `.opencode/rules/` <--symlink-- `domains/<category>/<domain>/rules/`

OMO's native config walking (`.opencode/` up to `$HOME`) handles the rest.

## When Working on This Repo

- Domain configs should contain ONLY rules/skills/agents content — NEVER model parameters
- Model configurations (providers, temperatures, etc.) belong in `~/.config/opencode/oh-my-openagent.jsonc` and are out of scope
- All domain directories follow the same structure: `{rules,agents,commands,mcp,skills}/`
- Use `vibe-stack activate <domain>` to test domain configs in a project
