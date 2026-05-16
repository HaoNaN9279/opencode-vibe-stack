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

## Directory layout

```
core/              Global config, A2A protocol/bus/orchestrator, combinator, rules, skills, MCP
platforms/         Windows / WSL2 / Linux — env vars, registries
domains/           Game-engine / DCC / Desktop / Web — each API-layer has module + agents + skills + rules
combinations/      Pre-built multi-domain bundles with composite orchestrators
scripts/           deploy.ps1, deploy.sh, update-stack.ps1, new-project.ps1
workspace-templates/  unity-project, multi-domain-project
```

## Adding a new module

```
domains/<category>/<tool>/<api-layer>/
├── module.opencode.md      # declares id, dependencies, provides, imports
├── agents/                 # agent definitions with a2a: blocks
├── skills/                 # skill definitions (YAML frontmatter + code body)
├── rules/                  # domain-specific coding rules
├── templates/              # code templates (optional)
└── mcp/                    # MCP server configs (optional)
```

All agents must declare A2A capabilities (`roles`, `capabilities`, `handles_tasks`, `composes`). Composite orchestrators live in `combinations/` and use `composes:` to reference domain-level orchestrators.
