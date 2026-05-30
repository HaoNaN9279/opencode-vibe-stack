# Vibe Stack

**Layered AI Agent Configuration Management for OpenCode + OhMyOpenAgent (OMO)**

When you develop across multiple domains (game dev, DCC tools, AI/data, web, mobile), your AI agent needs different rules, skills, and configurations for each. Vibe Stack isolates these into versioned, composable layers — without cluttering your user config directory.

## How It Works

```
┌─────────────────────────────────────────────┐
│  User Config (~/.config/opencode/)          │
│  └─ Symlinks → core/        (always loaded) │
├─────────────────────────────────────────────┤
│  Project Config (.opencode/)                │
│  ├─ Symlinks → domains/*/*  (per-project)   │
│  └─ opencode.json ← merged MCP + skills     │
├─────────────────────────────────────────────┤
│  Vibe Stack Repo (this repo)                │
│  ├── core/          ← resident configs      │
│  ├── domains/       ← domain-specific       │
│  │   ├── ai/                                │
│  │   │   └── data_forge/   (MCP, rules)     │
│  │   ├── dcc/                               │
│  │   │   ├── blender/                       │
│  │   │   ├── houdini/                       │
│  │   │   ├── maya/                          │
│  │   │   └── photoshop/   (agents, cmds)    │
│  │   └── game-dev/                          │
│  │       ├── unity/                         │
│  │       └── unreal/                        │
│  └── stacks/        ← preset combos         │
└─────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-org/opencode-vibe-stack.git ~/.opencode-vibe-stack
cd ~/.opencode-vibe-stack && bash install.sh

# 2. In any project, activate domains
vibe-stack activate ai/data_forge
vibe-stack activate dcc/blender

# 3. List available domains
vibe-stack list

# 4. Use a preset stack
vibe-stack use-stack game-dev
vibe-stack use-stack ai-training
```

## Configuration Layering

When you open a project in OpenCode with OMO, configs are loaded:

1. **Core** — Always loaded (global rules, shared skills, common agents)
2. **Project** — Your project's `.opencode/` directory
3. **Domain** — Activated via `vibe-stack activate` (per-project domain configs)

OMO handles merging automatically. Domain MCP configurations and skill registrations are merged into `.opencode/opencode.json`.

## What's Inside Each Domain

Each domain directory contains:

| Directory  | Purpose                          |
|------------|----------------------------------|
| `rules/`   | Domain-specific coding rules     |
| `agents/`  | Custom agent definitions         |
| `commands/`| Custom slash commands            |
| `mcp/`     | MCP server configs + binaries    |
| `skills/`  | Domain-tuned AI skills           |

> **MCP directories** may contain prebuilt binary releases (e.g., `data-forge.exe`) alongside`<domain>.json` config files for automatic MCP registration.

## Available Domains

| Category | Domain     | Description                          |
|----------|------------|--------------------------------------|
| `ai/`    | data_forge | Data transformation MCP server       |
| `dcc/`   | blender    | Blender 3D integration               |
| `dcc/`   | houdini    | Houdini FX integration               |
| `dcc/`   | maya       | Autodesk Maya integration            |
| `dcc/`   | photoshop  | Adobe Photoshop (agents, commands)   |
| `game-dev/` | unity   | Unity game engine integration        |
| `game-dev/` | unreal  | Unreal Engine integration            |

## Available Stacks

| Stack           | Included Domains                          |
|-----------------|-------------------------------------------|
| `game-dev`      | unity, unreal                             |
| `dcc`           | blender, houdini, maya, photoshop        |
| `ai-training`   | data_forge                                |
| `indie-game`    | unity, blender, data_forge               |
| `aaa-pipeline`  | unreal, maya, houdini, photoshop         |

## Adding New Domains

```bash
# Create the domain structure
mkdir -p domains/my-category/my-domain/{rules,agents,commands,mcp,skills}

# Add your rules, skills, etc.
echo "## My Domain Rules" > domains/my-category/my-domain/rules/my-domain.md

# If domain provides an MCP server, add config + binary
#   mcp/my-domain.json   → MCP registration
#   mcp/my-domain.exe    → prebuilt binary (optional)

# Commit and push
git add domains/my-category/ && git commit -m "feat: add my-domain configs" && git push
```

## Architecture Principles

- **Zero content in user config** — `~/.config/opencode/` only contains symlinks
- **Zero duplication** — One canonical source per domain, shared via symlinks
- **Git-versioned everything** — All configs are tracked in this repository
- **Model-agnostic** — Agent/category model parameters are out of scope (configured per machine)
- **Binary-based MCP** — MCP servers are prebuilt binaries, no Python/Node runtime required in projects
- **OMO-native** — Uses OMO's agent_definitions, command_definitions, and config walking
- **Skill registration via `opencode.json`** — Uses `skills.paths` (not OMO `skills.sources`)

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
3. Updates project `.opencode/opencode.json` with skill path references
4. Installs the `vibe-stack` CLI

## License

MIT
