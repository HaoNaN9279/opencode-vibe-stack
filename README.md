# Vibe Stack

**Layered AI Agent Configuration Management for OpenCode + OhMyOpenAgent (OMO)**

When you develop across multiple domains (game dev, DCC tools, web, mobile), your AI agent needs different rules, skills, and configurations for each. Vibe Stack isolates these into versioned, composable layers — without cluttering your user config directory.

## How It Works

```
┌─────────────────────────────────────────────┐
│  User Config (~/.config/opencode/)          │
│  └─ Symlinks → core/        (always loaded) │
├─────────────────────────────────────────────┤
│  Project Config (.opencode/)                │
│  └─ Symlinks → domains/*/*  (per-project)   │
├─────────────────────────────────────────────┤
│  Vibe Stack Repo (this repo)                │
│  ├── core/          ← resident configs      │
│  ├── domains/       ← domain-specific       │
│  │   ├── game-dev/                         │
│  │   │   ├── unity/                        │
│  │   │   └── unreal/                       │
│  │   └── dcc/                              │
│  │       ├── blender/                      │
│  │       ├── maya/                         │
│  │       └── houdini/                      │
│  └── stacks/        ← preset combos        │
└─────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-org/opencode-vibe-stack.git ~/.opencode-vibe-stack
cd ~/.opencode-vibe-stack && bash install.sh

# 2. In any project, activate domains
vibe-stack activate game-dev/unity

# 3. List available domains
vibe-stack list

# 4. Use a preset stack
vibe-stack use-stack game-dev
```

## Configuration Layering

When you open a project in OpenCode with OMO, configs are loaded:

1. **Core** — Always loaded (global rules, shared skills, common agents)
2. **Project** — Your project's `.opencode/` directory
3. **Domain** — Activated via `vibe-stack activate` (per-project domain configs)

OMO handles merging automatically.

## What's Inside Each Domain

Each domain directory contains:

| Directory  | Purpose                          |
|------------|----------------------------------|
| `rules/`   | Domain-specific coding rules     |
| `agents/`  | Custom agent definitions         |
| `commands/`| Custom slash commands            |
| `mcp/`     | MCP server configurations        |
| `skills/`  | Domain-tuned AI skills           |

## Adding New Domains

```bash
# Create the domain structure
mkdir -p domains/my-category/my-domain/{rules,agents,commands,mcp,skills}

# Add your rules, skills, etc.
echo "## My Domain Rules" > domains/my-category/my-domain/rules/my-domain.md

# Commit and push
git add domains/my-category/ && git commit -m "feat: add my-domain configs" && git push
```

## Architecture Principles

- **Zero content in user config** — `~/.config/opencode/` only contains symlinks
- **Zero duplication** — One canonical source per domain, shared via symlinks
- **Git-versioned everything** — All configs are tracked in this repository
- **Model-agnostic** — Agent/category model parameters are out of scope (configured per machine)
- **OMO-native** — Uses OMO's `skills.sources`, `agent_definitions`, and config walking

## Requirements

- OpenCode >= 1.15.x (latest recommended)
- OhMyOpenAgent (OMO) plugin installed
- Git
- Bash (Linux/macOS) or PowerShell (Windows)

## Installation

### Linux / macOS

```bash
bash install.sh
```

### Windows

```powershell
.\install.ps1
```

The installer:
1. Clones/updates this repo to `~/.opencode-vibe-stack`
2. Creates symlinks from `~/.config/opencode/` to `core/`
3. Updates OMO config with skill source references
4. Installs the `vibe-stack` CLI

## License

MIT
