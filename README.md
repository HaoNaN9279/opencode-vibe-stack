# Vibe Stack

**面向 OpenCode + OhMyOpenAgent (OMO) 的分层 AI 智能体配置管理**

当你在多个领域（游戏开发、DCC 工具、AI/数据、Web、移动端）进行开发时，你的 AI 智能体需要针对每个领域使用不同的规则、技能和配置。Vibe Stack 将这些配置隔离到版本化、可组合的层级中——而不弄乱你的用户配置目录。

## 工作原理

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

## 快速开始

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

## 配置分层

当你在 OpenCode 中使用 OMO 打开一个项目时，配置按以下顺序加载：

1. **Core（核心）** — 始终加载（全局规则、共享技能、通用智能体）
2. **Project（项目）** — 你项目的 `.opencode/` 目录
3. **Domain（领域）** — 通过 `vibe-stack activate` 激活（每个项目的领域配置）

OMO 自动处理合并。领域 MCP 配置和技能注册会被合并到 `.opencode/opencode.json` 中。

## 每个领域包含什么

每个领域目录包含：

| 目录        | 用途                              |
|-------------|-----------------------------------|
| `rules/`    | 领域特定的编码规则                |
| `agents/`   | 自定义智能体定义                  |
| `commands/` | 自定义斜杠命令                    |
| `mcp/`      | MCP 服务器配置 + 二进制文件       |
| `skills/`   | 领域调优的 AI 技能                |

> **MCP 目录** 可能包含预构建的二进制发布文件（如 `data-forge.exe`），以及用于自动 MCP 注册的 `<domain>.json` 配置文件。

## 可用领域

| 分类        | 领域       | 描述                                |
|-------------|------------|-------------------------------------|
| `ai/`       | data_forge | 数据转换 MCP 服务器                 |
| `dcc/`      | blender    | Blender 3D 集成                     |
| `dcc/`      | houdini    | Houdini FX 集成                     |
| `dcc/`      | maya       | Autodesk Maya 集成                  |
| `dcc/`      | photoshop  | Adobe Photoshop（智能体、命令）     |
| `game-dev/` | unity      | Unity 游戏引擎集成                  |
| `game-dev/` | unreal     | Unreal Engine 集成                  |

## 可用堆栈

| 堆栈             | 包含的领域                                |
|------------------|-------------------------------------------|
| `game-dev`       | unity, unreal                             |
| `dcc`            | blender, houdini, maya, photoshop        |
| `ai-training`    | data_forge                                |
| `indie-game`     | unity, blender, data_forge               |
| `aaa-pipeline`   | unreal, maya, houdini, photoshop         |

## 添加新领域

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

## 架构原则

- **用户配置零内容** — `~/.config/opencode/` 只包含符号链接
- **零重复** — 每个领域只有一个权威来源，通过符号链接共享
- **一切 Git 版本化** — 所有配置都在此仓库中追踪
- **模型无关** — 智能体/分类的模型参数不在范围之内（按机器配置）
- **基于二进制文件的 MCP** — MCP 服务器是预构建的二进制文件，项目中不需要 Python/Node 运行时
- **OMO 原生** — 使用 OMO 的 agent_definitions、command_definitions 和配置遍历
- **通过 `opencode.json` 注册技能** — 使用 `skills.paths`（而非 OMO 的 `skills.sources`）

## 环境要求

- OpenCode >= 1.15.x（推荐最新版本）
- 已安装 OhMyOpenAgent (OMO) 插件
- Git
- Bash（Linux/macOS）或 PowerShell（Windows）

## 安装

### Linux / macOS

```bash
bash install.sh
```

### Windows

```powershell
.\install.ps1
```

安装程序将：
1. 克隆/更新此仓库到 `~/.opencode-vibe-stack`
2. 从 `~/.config/opencode/` 创建到 `core/` 的符号链接
3. 更新项目 `.opencode/opencode.json` 中的技能路径引用
4. 安装 `vibe-stack` CLI

## 许可证

MIT
