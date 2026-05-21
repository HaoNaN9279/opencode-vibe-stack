# OpenCode Vibe Coding 工具链

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

部署脚本会逐个链接 core 下的内容到 OpenCode 配置目录：

```
core/agents/*.md           →  ~/.config/opencode/agents/
core/rules/*.md            →  ~/.config/opencode/rules/
core/skills/<name>/         →  ~/.config/opencode/skills/<name>/
core/commands/*.md         →  ~/.config/opencode/commands/
core/mcp/mcp-config.json    →  ~/.config/opencode/mcp-config.json
core/domain.config          →  ~/.config/opencode/domain.config
```

支持重复执行：自动同步新增、修改和删除的文件，清理过期链接。

### 1.4 配置 opencode.json

将以下内容合并到 `~/.config/opencode/opencode.json`：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": { ... },
  "default_agent": "QuickQA",
  "mcp": "{file:mcp-config.json}",
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

Skills 自动从 `~/.config/opencode/skills/` 发现，无需显式声明 skills.paths。

---

## 二、加载架构

### 2.1 Core（常驻，逐个链接）

Core 下的内容通过部署脚本逐个链接到 `~/.config/opencode/` 的扁平目录，OpenCode 启动时自动发现：

| 内容 | 位置 | 发现方式 |
|------|------|----------|
| agents | `~/.config/opencode/agents/*.md` | OpenCode 自动发现 |
| rules | `~/.config/opencode/rules/*.md` | OpenCode 自动发现 |
| skills | `~/.config/opencode/skills/<name>/SKILL.md` | OpenCode 自动发现 |
| commands | `~/.config/opencode/commands/*.md` | OpenCode 自动发现 |
| MCP | `~/.config/opencode/mcp-config.json` | opencode.json 引用 |
| domain 注册表 | `~/.config/opencode/domain.config` | workspace_init 读取 |

无法直嵌套目录：所有 agent、rule、skill 文件必须直接在对应目录下。

### 2.2 Domains（按项目链接）

Domain 模块位于 `domains/` 目录下。在项目目录中通过 OpenCode 运行 `workspace_init` 命令，explore agent 会自动：
1. 扫描项目文件识别技术栈
2. 从 `domain.config` 匹配需要的模块
3. 将模块内容逐个链接到项目 `opencode/agents/`、`opencode/rules/`、`opencode/skills/`
4. 生成 `opencode/workspace.md`

Agent 链接时添加 domain 前缀（如 `unity.csharp.orchestrator.md`）避免不同 module 的同名 agent 冲突。

### 2.3 加载优先级

```
project (最高) > domains > core (基础)
```

- 项目的 `opencode/` 内容优先级最高
- 同名 agent/skill/rule 按优先级覆盖

---

## 三、在项目中使用

### 3.1 初始化工作空间

在项目目录中，通过 OpenCode 运行：

> 初始化工作空间

系统会自动识别项目类型并链接匹配的 domain 模块。

### 3.2 手动配置

也可以直接编辑 `opencode/workspace.md`：

```yaml
---
version: "2.1"
name: "MyGame"
domains:
  - "game-engine.unity.csharp-api"
  - "game-engine.unity.editor"
---
```

### 3.3 在 Chat 中使用

部署完成后，直接在 OpenCode 对话中即可使用：

> "帮我创建一个 Unity 角色控制器组件"
> "写一个 Blender 插件，批量导出 FBX"
> "做一个 Express REST API，用户增删改查"

---

## 四、后期维护

### 4.1 更新工具链

```bash
cd $OPCODE_STACK_ROOT
git pull origin main
./scripts/deploy.sh    # 重新同步链接 + 更新 domain.config
```

### 4.2 更新项目 domain 链接

在项目目录中重新运行 `workspace_init` 自动刷新。

### 4.3 在另一台机器上部署

```bash
git clone <仓库地址>
./scripts/deploy.sh    # 或 deploy.ps1
```

---

## 五、扩展（添加新模块）

### 5.1 添加新 domain 模块

在 `domains/` 下创建目录结构（2-3 层深度）：

```
domains/<领域>/<软件>/<语言或API层>/
├── agents/
│   └── my-agent.md
├── commands/
│   └── my-command.md
├── rules/
│   └── my-standards.md
└── skills/
    └── my-pattern/
        └── SKILL.md
```

重新运行 `deploy.sh` 即可更新 `domain.config` 注册。

### 5.2 添加新 Agent

在对应模块的 `agents/` 目录下创建 `*.md`：

```yaml
---
name: domain.tool.agent-name
description: 简要描述 Agent 的功能和适用场景
mode: subagent

a2a:
  enabled: true
  roles: [角色]
  capabilities: [能力1, 能力2]
---

你是一位怎样的专家。
具体的行为规则、专业知识、工作流程等。
```

### 5.3 添加新 Skill

在对应模块的 `skills/` 下创建 `<name>/SKILL.md`：

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

### 5.4 添加自研 MCP 服务

在 `core/mcp/` 下创建独立项目目录，在 `core/mcp/mcp-config.json` 中注册。

---

## 六、目录速查

| 路径 | 用途 | 加载方式 |
|------|------|----------|
| `core/agents/` | 通用 agent | deploy.sh 链接到 ~/.config/opencode/agents/ |
| `core/commands/` | 全局命令 | deploy.sh 链接到 ~/.config/opencode/commands/ |
| `core/rules/` | 全局规则（含 combinator、A2A 协议） | deploy.sh 链接到 ~/.config/opencode/rules/ |
| `core/skills/` | 通用技能模板 | deploy.sh 链接到 ~/.config/opencode/skills/ |
| `core/mcp/` | MCP 配置和自研项目 | mcp-config.json 链接到 ~/.config/opencode/ |
| `core/domain.config` | 领域模块注册表 | 链接到 ~/.config/opencode/，workspace_init 读取 |
| `domains/` | 领域模块 | workspace_init 按需链接到项目 opencode/ |
| `scripts/` | 部署脚本 | - |
