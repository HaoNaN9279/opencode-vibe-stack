# OpenCode Vibe Coding 工具链使用指南

## 一、部署

### 1.1 前置条件

- 已安装 OpenCode
- 已安装 Git

### 1.2 克隆仓库

```bash
git clone <仓库地址> ~/opencode-vibe-stack
cd ~/opencode-vibe-stack
```

### 1.3 一键部署

**Linux / WSL2**：

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**Windows**（以管理员身份运行 PowerShell）：

```powershell
.\scripts\deploy.ps1
```

会做两件事：
1. 设置环境变量 `OPCODE_STACK_ROOT`
2. 在 `~/.config/opencode/User/` 下创建 `core` 符号链接

### 1.4 配置 opencode.json

将以下内容合并到 `~/.config/opencode/opencode.json`（最小示例）：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": { ... },
  "default_agent": "QuickQA",
  "skills": {
    "paths": ["User/core/skills"]
  },
  "mcp": {
    "filesystem": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "git": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-git", "."]
    },
    "docsetmcp": {
      "type": "local",
      "command": ["uvx", "docsetmcp"],
      "env": {
        "DOCSET_PATH": "/mnt/d/workspace/docsets",
        "CHEATSHEET_PATH": "/mnt/d/workspace/cheatsheets"
      }
    }
  },
  "agent": {
    "QuickQA": {
      "mode": "primary",
      "description": "快速问答（读/搜，不可写）",
      "permission": {
        "read": "allow", "edit": "deny", "bash": "deny", "task": "deny"
      }
    }
  }
}
```

### 1.5 验证部署

重启 OpenCode 后配置即生效。

---

## 二、加载架构

### 2.1 Core（常驻）

`User/core/` symlink → `${OPCODE_STACK_ROOT}/core/`。OpenCode 启动时自动发现该目录下所有 `*.opencode.md`：

- **agents** — `QuickQA` 等通用 agent
- **skills** — `code-review`, `code-refactor`, `debugging`
- **rules** — 全局 vibe coding / security / naming 规则
- **MCP** — git, filesystem
- **A2A** — 协议/总线/编排器/注册表

无需 workspace 文件即可生效。

### 2.2 Domains（按需）

只在项目 workspace 文件中通过 `imports:` 按需加载。例如 Unity 项目：

```yaml
---
imports:
  - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/editor/module.opencode.md"
---
```

`editor/module.opencode.md` 会自动级联加载依赖的 `csharp-api/module.opencode.md`，以及各自的 agents/skills/rules。

MCP 也按 workspace 声明选择性加载，不在启动时全部启动。

### 2.3 快速参考

| 问题 | 答案 |
|------|------|
| 不打开项目能用 core 吗？ | 能，启动即加载 |
| 怎么加载 Unity agent？ | 项目下放 workspace 文件，只 import 一个 editor module |
| core MCP 何时加载？ | 全局常驻 |
| domain MCP 何时加载？ | 跟随 workspace 声明 |

---

## 三、在项目中使用

### 3.1 创建新项目

```bash
# Windows
.\scripts\new-project.ps1 -ProjectName MyGame -Template unity
```

或手动在项目根目录创建 `.opencode/workspace.opencode.md`：

```yaml
---
version: "2.1"
name: "MyGame"
type: "unity-project"

imports:
  - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/editor/module.opencode.md"

agents:
  default: "unity.csharp.orchestrator"

mcp_servers:
  - "mcp://unity-editor"

skills:
  paths:
    - "${OPCODE_STACK_ROOT}/domains/game-engine/unity/csharp-api/skills"
---
```

### 3.2 多领域组合项目

如果项目同时使用 Unity + Blender + Node.js：

```yaml
---
version: "2.1"
name: "MyGameToolchain"
type: "multi-domain"

domains:
  - "game-engine.unity.csharp-api"
  - "dcc.blender.python-api"
  - "web.nodejs.express"

# 或直接用预定义的组合包
imports:
  - "${OPCODE_STACK_ROOT}/combinations/game-asset-pipeline/combination.opencode.md"

agents:
  default: "game-asset-pipeline.orchestrator"
---
```

### 3.3 在 Chat 中使用

部署完成后，直接在 OpenCode 对话中使用即可：

> "帮我创建一个 Unity 角色控制器组件"
> "写一个 Blender 插件，批量导出 FBX"
> "做一个 Express REST API，用户增删改查"

系统会自动加载对应领域的 Agent 和技能来处理。

---

## 四、后期维护

### 4.1 更新工具链

```bash
cd $OPCODE_STACK_ROOT
git pull origin main
```

### 4.2 只更新特定模块

```powershell
.\scripts\update-stack.ps1 -Module game-engine.unity.csharp-api
```

### 4.3 在另一台机器上部署

```bash
git clone <仓库地址>
./scripts/deploy.sh    # 或 deploy.ps1
```

五分钟内即可恢复完整环境。

---

## 五、扩展（添加新模块）

### 5.1 快速添加新 API 层

在对应领域目录下创建子目录和 `module.opencode.md`：

```
domains/<领域>/<工具>/<API层>/
├── module.opencode.md
├── agents/
├── skills/
├── rules/
├── templates/
└── mcp/
```

### 5.2 module.opencode.md 模板

```yaml
---
version: "2.1"
module:
  id: "领域.工具.API层"        # 唯一标识
  name: "显示名称"
  description: "描述"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["语言1"]
    apis: ["API名称"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
```

### 5.3 添加新 Agent

在对应模块的 `agents/` 目录下创建 `*.opencode.md`：

```yaml
---
version: "2.1"
agent:
  id: "领域.工具.API层.agent-name"
  name: "显示名称"

  a2a:
    enabled: true
    roles: ["角色"]
    capabilities: ["能力1", "能力2"]
    handles_tasks: ["可处理的任务"]
    depends_on: ["其他Agent ID"]

  persona: |
    你是一位怎样的专家。
---
```

### 5.4 添加新 Skill

在对应模块的 `skills/` 目录下创建 `*.opencode.md`，代码模板放在 `---` 下方。

### 5.5 添加新 MCP 服务

各 MCP 项目环境隔离：网络 MCP 用 uvx/npx 不存源码，自研 MCP 独立 git 项目 + 自有 venv/node_modules。

#### 声明式注册（`core/mcp/*.opencode.md`）— 推荐

MCP 服务通过 `core/mcp/<name>.opencode.md` 文件声明，OpenCode 启动时自动发现并加载，无需修改 `opencode.json`：

```yaml
---
version: "2.1"
mcp_server:
  name: "<name>"
  type: "local"
  command: "uvx"
  args: ["<package>"]
  env:
    VAR_NAME: "/path/to/dir"
  description: "描述"
  capabilities:
    - "tool1"
    - "tool2"
---
```

`opencode.json` 中只需保留基础设施类 MCP（filesystem、git），其余 MCP 全部通过此方式注册。

#### 网络 MCP（Python）

直接使用 `uvx`，无需本地维护源码和虚拟环境：

1. 在 `core/mcp/<name>.opencode.md` 中声明（见上方声明式注册）
2. 如需配置文件，放入 `core/mcp/<name>/`

#### 网络 MCP（Node.js）

```bash
"mcp": {
  "<name>": {
    "type": "local",
    "command": ["npx", "-y", "<name>"]
  }
}
```

#### 自研 MCP（Python）

作为独立 git 项目放在 `core/mcp/<name>/`，拥有独立的虚拟环境：

```
core/mcp/<name>/
├── .git/              ← 独立仓库
├── pyproject.toml     ← 定义 [project.scripts] 入口
├── src/
├── .venv/             ← 部署时 uv sync 生成，已 gitignored
└── README.md
```

`opencode.json` 注册（推荐 `bash -c` 包装以展开环境变量）：

```json
"<name>": {
  "type": "local",
  "command": ["bash", "-c", "cd $OPCODE_STACK_ROOT/core/mcp/<name> && uv run <name>"]
}
```

或直接用绝对路径：

```json
"<name>": {
  "type": "local",
  "command": ["uv", "run", "--directory", "/abs/path/to/core/mcp/<name>", "<name>"]
}
```

#### 自研 MCP（Node.js）

同理，独立 git 项目 + 独立 `node_modules/`：

```
core/mcp/<name>/
├── .git/
├── package.json
├── src/
├── node_modules/      ← npm install 生成，已 gitignored
└── README.md
```

`opencode.json` 注册：

```json
"<name>": {
  "type": "local",
  "command": ["node", "/abs/path/to/core/mcp/<name>/server.js"]
}
```

---

## 六、目录速查

| 路径 | 用途 | 加载方式 |
|------|------|----------|
| `core/` | 全局通用配置、agent、skill、rule、MCP、A2A | 启动常驻 |
| `platforms/` | 平台配置（Windows/Linux/WSL2） | 按平台条件 |
| `domains/dcc/` | DCC软件（Blender/Houdini/Maya） | 按 workspace |
| `domains/game-engine/` | 游戏引擎（Unity/Unreal） | 按 workspace |
| `domains/desktop/` | 桌面开发（C#/C++/Python） | 按 workspace |
| `domains/web/` | Web开发（Node.js/React/Vue） | 按 workspace |
| `combinations/` | 预定义的跨领域组合包 | 按 workspace |
| `scripts/` | 部署和项目初始化脚本 | - |
| `workspace-templates/` | 项目模板 | - |
