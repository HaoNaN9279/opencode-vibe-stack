# opencode-vibe-stack

**Configuration-only** repo for OpenCode v2.1 Vibe Coding. No code to build/test/lint/run. No CI, no packaged dependencies, no tooling configs.

## First reads

- `AI给出的方案.md` — canonical design doc in Chinese, covers the full architecture
- `使用指南.md` — beginner usage guide (deploy / use / extend)

## What an agent will get wrong without this

- **No tests, no build.** There is no test runner, no npm test, no Makefile. Nothing to execute.
- **File format is `*.opencode.md`**, not `.yaml` or `.json`. YAML lives inside `---` frontmatter; the body below `---` is docs or code templates.
- **No git history yet.** The repo has never been committed. Expect zero git context.
- **Deployment is via symbolic links**, not copy. Repo lives in one place; `~/.config/opencode/User/` contains symlinks pointing into it.
- **`${OPCODE_STACK_ROOT}`** must be set to the repo root. Every cross-file import depends on this.
- **Module IDs** (`domain.subdomain.api-layer`, e.g. `dcc.blender.plugins`) are used as identifiers throughout — agents, skills, and imports all reference each other by ID.
- **Imports** use glob patterns: `./skills/*.opencode.md`.
- **Everything is in Chinese** — spec, comments, agent personas, skill descriptions.
- **No external plugins allowed.** This stack is 100% native `*.opencode.md` by design.

## Loading architecture

- **Core (always)** — `~/.config/opencode/User/core/` symlink → `${OPCODE_STACK_ROOT}/core/`. OpenCode auto-discovers all `*.opencode.md` under User/ at startup. All core agents, skills, rules, MCP configs, A2A, and combinator are loaded globally without any workspace file.
- **Domains (per-project)** — Workspace `.opencode/workspace.opencode.md` imports domain modules via `${OPCODE_STACK_ROOT}/domains/...`. Domain agents, skills, and MCP are loaded only when the workspace is active.
- **MCP servers** — Core MCP (git, filesystem) defined in `opencode.json` `mcp` field. Domain MCP (e.g., unity-editor) declared in workspace `mcp_servers:`.
- **Skills** — Core skills registered in `opencode.json` `skills.paths`. Domain skills registered in workspace `skills:` → `paths:` (only available per-project).
- **Module files** (`module.opencode.md`) MUST import `./agents/*.opencode.md` alongside skills/rules/templates/mcp — otherwise agents won't be loaded even when the module is imported.

## Directory layout

```
core/              Always-on: agents, skills, rules, MCP, A2A, combinator
platforms/         Windows / WSL2 / Linux — env vars, registries
domains/           Per-project: game-engine / DCC / Desktop / Web
combinations/      Pre-built multi-domain bundles
scripts/           deploy.sh, new-project.ps1, update-stack.ps1
workspace-templates/  unity-project, multi-domain-project
```

## Adding a new module

```
domains/<category>/<tool>/<api-layer>/
├── module.opencode.md      # imports: agents, skills, rules, templates, mcp
├── agents/                 # agent definitions with a2a: blocks
├── skills/                 # skill definitions (YAML frontmatter + code body)
├── rules/                  # domain-specific coding rules
├── templates/              # code templates (optional)
└── mcp/                    # MCP server configs (optional)
```

All agents must declare A2A capabilities (`roles`, `capabilities`, `handles_tasks`, `composes`). Composite orchestrators live in `combinations/` and use `composes:` to reference domain-level orchestrators.
