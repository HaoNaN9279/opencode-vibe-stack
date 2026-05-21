# AGENTS.md

## 项目概述

OpenCode Vibe Coding 工具链 — 为 OpenCode 提供可组合的领域 agent、skill、rule、command 模块。
通过 deploy 脚本将 core 内容逐个链接到 `~/.config/opencode/`，workspace_init 命令按项目类型按需链接 domain 模块。

- 语言：Markdown + YAML（配置）、Bash（deploy.sh）、PowerShell（deploy.ps1）、Python（domain.config 生成）
- 目标运行时：OpenCode CLI >= 2.0
- 无需编译，纯配置文件构成

## 构建与安装

```bash
# 部署到本地 OpenCode 配置目录
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Windows
.\scripts\deploy.ps1
```

部署脚本无依赖，仅需 bash >= 4.0 或 PowerShell 5.1+。Python 3 用于生成 domain.config（已内联在 deploy.sh / deploy.ps1 中）。

## 测试验证

```bash
./scripts/deploy.sh    # 重复执行验证幂等性
```

验证项：
- `~/.config/opencode/agents/` 应包含 3 个 `.md` 文件
- `~/.config/opencode/rules/` 应包含 1 个 `.md` 文件
- `~/.config/opencode/skills/` 应包含 3 个子目录
- `~/.config/opencode/commands/` 应包含 1 个 `.md` 文件
- `~/.config/opencode/domain.config` 应注册 6 个模块
- 再次执行 deploy.sh 应全部跳过（幂等）

## 项目结构

```
opencode-vibe-stack/
├── core/                        # 常驻内容，部署到 ~/.config/opencode/
│   ├── agents/                  # 全局 agent 定义（*.md）
│   ├── rules/                   # 全局规则（*.md）
│   ├── skills/                  # 全局 skill（<name>/SKILL.md）
│   ├── commands/                # 全局命令（*.md）
│   ├── mcp/                     # MCP 配置（mcp-config.json）
│   └── domain.config            # 领域模块注册表（JSON，由 deploy.sh 自动生成）
├── domains/                     # 领域模块，workspace_init 按需链接
│   └── <领域>/<软件>/<语言>/
│       ├── agents/
│       ├── rules/
│       ├── skills/
│       └── commands/
├── scripts/
│   ├── deploy.sh                # Linux/WSL2 部署
│   └── deploy.ps1               # Windows 部署
└── README.md
```

### 加载优先级

```
project (最高) > domains > core (基础)
```

同名 agent/skill/rule 按优先级覆盖。combinator 引擎合并策略见 `core/rules/global.md`。

### 部署链路

```
core/agents/*.md       → ln → ~/.config/opencode/agents/
core/rules/*.md        → ln → ~/.config/opencode/rules/
core/skills/<name>/    → ln → ~/.config/opencode/skills/<name>/
core/commands/*.md     → ln → ~/.config/opencode/commands/
core/mcp/mcp-config.json → ln → ~/.config/opencode/mcp-config.json
core/domain.config     → ln → ~/.config/opencode/domain.config

domains/<D.path>/agents/*.md → ln → <project>/opencode/agents/<D.name>.<原文件名>
domains/<D.path>/rules/*.md  → ln → <project>/opencode/rules/<原文件名>
domains/<D.path>/skills/*/   → ln → <project>/opencode/skills/<原文件名>/
```

## 编写规范

### Agent（agents/*.md）

Agent 使用 Markdown 文件定义，文件名即 agent 名称。YAML frontmatter 包含配置，body 为系统 prompt。

**必需字段：** `description`、`mode`（`primary` 或 `subagent`）

**可选字段：** `tools`（write/edit/task/bool 布尔值）、`temperature`、`model`、`steps`、`hidden`、`permission`

**域元数据（自定义字段，保留给 workspace_init 使用）：** `a2a`（roles、capabilities、manages_agents、depends_on）、`task_flows`、`skills`

```yaml
---
name: domain.tool.role-name
description: 简要描述 Agent 的功能和适用场景（必填）
mode: subagent

a2a:
  enabled: true
  roles: [role-name]
  capabilities: [capability-1, capability-2]
---

你是一位特定领域的专家。
具体的行为规则、专业知识、工作流程写在此处。
```

**示例（来自 `core/agents/dynamic-orchestrator.md`）：**

```yaml
---
name: dynamic-orchestrator
description: 动态任务编排器，将复杂多领域任务分解为可执行的子任务，查询可用 Agent 并分配执行
mode: subagent

a2a:
  enabled: true
  roles: [orchestrator, planner]
  capabilities: [analyze-complex-task, generate-execution-plan, query-agent-capabilities, assign-subtasks, aggregate-results, cross-domain-planning]

workflow:
  - analyze: 分析任务涉及的领域和技术栈，确定所需的 agent 能力
  - discover: 查询 agent registry 获取当前可用的 agent 列表及其能力
  - plan: 根据任务需求与可用 agent 能力，动态生成最优执行计划
  - assign: 将子任务分配给能力最匹配的 agent
  - monitor: 监控子任务执行进度，处理异常情况
  - aggregate: 收集并整合所有子任务的结果，形成最终输出
---

你是一位经验丰富的任务编排专家。
你擅长将复杂的多领域任务分解为可执行的子任务。
你会动态查询系统中当前可用的 Agent 及其能力。
你能够识别跨领域任务的依赖关系和最优执行顺序。
你不会依赖预设的任务流程，而是根据实际情况动态规划。
```

**模式说明：**
- `primary` — 主代理，用户直接交互，可切换（仅 QuickQA 使用）
- `subagent` — 子代理，由主代理通过 Task 工具调用，或用户 @ 提及（所有其他 agent）
- `hidden: true` — 从 @ 菜单隐藏，仅限 Task 工具调用

**工具控制：** `tools: { write: true, edit: true }` 授权写操作。生成类 agent 开启，分析/审查类关闭。

---

### Rule（rules/*.md）

Rule 是纯 Markdown 文件，作为系统指令注入。无 frontmatter，直接使用标题和列表描述规范。

```markdown
# 规范标题

- 规则条目 1
- 规则条目 2
- 规则条目 3
```

**示例（来自 `domains/game-engine/unity/csharp-api/rules/unity-standards.md`）：**

```markdown
# Unity C# 编码规范

- 避免在 Update 中创建新对象（减少 GC 压力）
- 使用对象池管理频繁创建销毁的对象
- 用 TryGetComponent 代替 GetComponent 判空
- 缓存 GetComponent 引用
- 使用 Input System 包替代旧的 Input Manager
- 使用 Addressables 管理资源加载
- 优先使用 Data-Oriented 设计（ECS）处理大量实体
- 使用 SerializeReference 替代 ScriptableObject 的多态需求
```

**约束：**
- 每条规则占一行，以 `- ` 开头
- 规则描述简短（一行），不解释原理
- 每组规则用一个 `#` 标题区分
- 规则文件中不要写 YAML frontmatter

---

### Skill（skills/&lt;name&gt;/SKILL.md）

Skill 是 `skills/<name>/SKILL.md` 格式的目录结构。`<name>` 仅能用小写字母+数字+连字符。YAML frontmatter 包含元数据，body 为 skill 内容。

**必需字段：** `name`、`description`

**可选字段：** `license`、`compatibility`、`metadata`

```yaml
---
name: skill-name
description: 技能描述（1-1024 字符）
license: MIT
compatibility: opencode
metadata:
  domain: domain.tool.language
---

## What I do

描述该技能。

## When to use me

说明何时使用。
```

**示例（来自 `core/skills/code-review/SKILL.md`）：**

```yaml
---
name: code-review
description: 审查代码质量，覆盖安全性、性能和可维护性四个维度，输出问题清单和改进建议
license: MIT
compatibility: opencode
---

## What I do

审查代码质量，输出问题清单和改进建议。

## When to use me

当用户要求 review、审查或检查代码质量时使用。
```

**约束：**
- `<name>` 必须符合 kebab-case：仅 `[a-z0-9-]`
- 文件必须命名为 `SKILL.md`，位于同名目录内
- `description` 不超过 1024 字符
- 不允许嵌套子目录

---

### Command（commands/*.md）

Command 使用 Markdown 文件定义，YAML frontmatter 声明元数据，body 为执行指令。文件名即命令名。

```yaml
---
description: 命令描述
agent: 默认执行的 agent 名称
---
```

**示例（来自 `core/commands/workspace_init.md` fragment）：**

```markdown
---
description: "扫描当前项目，自动识别所需的技术领域，并链接对应的 domain 模块到项目 opencode/ 目录"
agent: build
---

# workspace_init

## 概述

扫描当前项目目录，通过 explore agent 识别项目类型和技术栈，
从 `domain.config` 中匹配需要的 domain 模块，
以逐个文件/目录链接的方式安装到项目的 `opencode/` 目录下。

## 执行步骤

### 1. 探索项目

使用 explore agent 扫描当前目录：
- 检查配置文件（package.json、*.csproj、CMakeLists.txt 等）
- 检查源代码文件类型
- 检查特定目录结构

### 2. 匹配 domain

读取 `~/.config/opencode/domain.config`，将探索结果交叉匹配。

### 3. 链接 domain 到项目

对每个匹配的 domain，遍历其子目录并链接到项目 `opencode/`。
Agent 链接时添加 domain 前缀（如 `unity.csharp.orchestrator.md`）。
```

**约束：**
- `description` 必填，简短说明命令功能
- `agent` 指定触发哪个 agent 执行（如 `build`）
- body 内容应包含清晰的分步执行指令

---

## Domain 模块结构

每个 domain 模块位于 `domains/<领域>/<软件>/<语言>/`，三层深度，必含至少一个非空子目录：

```
domains/game-engine/unity/csharp-api/
├── agents/
│   ├── orchestrator.md
│   ├── code-generator.md
│   ├── architecture-designer.md
│   └── ...
├── rules/
│   └── unity-standards.md
└── skills/
    ├── scriptable-object/
    │   └── SKILL.md
    └── component/
        └── SKILL.md
```

`domain.config` 由 `deploy.sh` 自动扫描 `domains/` 生成，类型推断规则在脚本内 `DEFAULT_INDICATORS` 和 `TYPE_MAP` 中维护。新增 domain 后重新运行 `deploy.sh` 即可注册。

## 文件命名约定

| 类型 | 位置 | 命名规则 |
|------|------|----------|
| Agent | `agents/<name>.md` | kebab-case，文件名即 agent 名 |
| Rule | `rules/<name>.md` | kebab-case |
| Skill | `skills/<name>/SKILL.md` | `<name>` 仅 `[a-z0-9-]`，目录名即 skill 名 |
| Command | `commands/<name>.md` | snake_case，文件名即命令名 |
| Domain agent（项目链接后） | `opencode/agents/<D.name>.<原名>.md` | 以 domain 名全称为前缀 |

## 安全规则

- 禁止在配置文件中硬编码密钥、token、密码
- `mcp-config.json` 中的 API key 必须通过环境变量引用
- deploy 脚本仅创建 symlink，不修改源文件
- 提交前确保无 `.env`、`.local` 等敏感文件

## 不要做的事

- 不要手动编辑 `core/domain.config`（由 deploy.sh 自动生成）
- 不要将 skills 文件直接放在 `skills/` 下（必须在同名子目录内）
- 不要在 rule 文件中的 Markdown 内容里写入 YAML frontmatter
- 不要在 agent 文件的 frontmatter 内使用 `version: "2.1"` 或嵌套 `agent:` 结构
- 不要使用 `.opencode.md` 后缀（统一 `.md`）
- 不要破坏 deploy.sh 的幂等性（每次改动后验证部署结果）
