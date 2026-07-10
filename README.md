# Vibe Stack

**面向 OpenCode 的分层 AI 智能体配置管理**

当你在多个领域（游戏开发、DCC 工具、AI/数据）进行开发时，你的 AI 智能体需要针对每个领域使用不同的规则、技能和配置。Vibe Stack 将这些配置隔离到版本化、可组合的层级中——而不弄乱你的项目配置目录。

## 工作原理

```
┌─────────────────────────────────────────────────┐
│  User Config (~/.config/opencode/)              │
│  └─ File copy ← core/          (sync 触发)      │
├─────────────────────────────────────────────────┤
│  Project Config (.opencode/)                    │
│  ├─ File copy ← domains/**/*    (activate 触发) │
│  │   └─ 命名空间子目录隔离 (rules/dcc_blender/)  │
│  ├─ .vibe-stack-state.json  ← 所有权追踪        │
│  └─ opencode.json ← 合并 instructions/skills/MCP│
├─────────────────────────────────────────────────┤
│  Vibe Stack Repo (this repo)                    │
│  ├── core/          ← 常驻配置                  │
│  ├── domains/       ← 领域定义（任意深度嵌套）    │
│  │   ├── ai/                                    │
│  │   │   └── data-forge/  (domain.json)         │
│  │   ├── dcc/                                   │
│  │   │   ├── blender/      (domain.json)        │
│  │   │   ├── houdini/                           │
│  │   │   ├── maya/                              │
│  │   │   └── photoshop/                         │
│  │   └── game-dev/                              │
│  │       ├── unity/                             │
│  │       └── unreal/                            │
│  └── stacks/        ← 预定义领域组合             │
│  └── tools/          ← 共享工具代码（集中管理）     │
└─────────────────────────────────────────────────┘
```

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/opencode-vibe-stack.git ~/.opencode-vibe-stack

# 2. 安装 Python 依赖
cd ~/.opencode-vibe-stack && uv sync

# 3. 初次同步（Core → ~/.config/opencode/）
uv run vibe-stack sync
```

## 日常使用

```bash
# 在项目中激活领域
cd my-project
vibe-stack activate dcc/blender ai/data-forge

# 查看激活状态
vibe-stack status

# 查看领域详情
vibe-stack info dcc/blender

# 源配置更新后，同步到项目
vibe-stack sync

# 停用领域
vibe-stack deactivate dcc/blender

# 使用预设堆栈
vibe-stack use-stack game-dev
```

## 核心概念

### 配置分层

当你在 OpenCode 中打开一个项目时，配置按以下顺序加载：

1. **Core（核心）** — 全局规则和共享技能，通过 `vibe-stack sync` 同步到 `~/.config/opencode/`
2. **Project（项目）** — 你项目的 `.opencode/` 目录，项目专有内容永不被修改
3. **Domain（领域）** — 通过 `vibe-stack activate` 按需激活，领域文件被**拷贝**到命名空间子目录中

配置变更后需显式运行 `vibe-stack sync` 才会传播到项目中。

### 领域（Domain）—— 最小配置单元

每个领域通过 `domain.json` 自描述，支持任意深度嵌套。通过 `domains/**/domain.json` 递归发现，不限制目录层级。

```jsonc
// domains/dcc/blender/domain.json
{
  "name": "blender",
  "description": "Blender 3D creation suite integration",
  "version": "1.0.0",
  "tags": ["dcc", "3d", "blender"],
  "dependencies": []
}
```

领域键由目录相对路径自动推导：`domains/dcc/blender/domain.json` → 键: `dcc/blender`。

### 命名空间（Namespace）—— 防冲突隔离

每个领域激活后在 `.opencode/` 下拥有独立子目录：

```
领域键: dcc/blender → 命名空间: dcc_blender

.opencode/rules/dcc_blender/           ← 独立目录
.opencode/agents/dcc_blender/
.opencode/commands/dcc_blender/
.opencode/mcp/dcc_blender/
.opencode/skills/dcc_blender/
```

文件名保持不变，删除领域时直接移除整个命名空间目录。

### 所有权（Ownership）—— 项目内容保护

`.opencode/.vibe-stack-state.json` 记录 vibe-stack 拥有的全部内容。停用时精确删除，项目专有内容永不被触碰。

## 每个领域包含什么

| 目录        | 用途                              |
|-------------|-----------------------------------|
| `rules/`    | 领域特定的编码规则                |
| `agents/`   | 自定义智能体定义                  |
| `commands/` | 自定义斜杠命令                    |
| `mcp/`      | MCP 服务器配置                    |
| `skills/`   | AI 技能（含内嵌工具代码）          |

> 工具代码不再独立为 `tools/` 目录，而是内嵌在对应的 `skills/{name}/tools/` 中。

## 可用领域

| 分类        | 领域       | 描述                                |
|-------------|------------|-------------------------------------|
| `ai/`       | data-forge | 数据转换 MCP 服务器                 |
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
| `ai-training`    | data-forge                                |
| `indie-game`     | unity, blender, data-forge               |
| `aaa-pipeline`   | unreal, maya, houdini, photoshop         |

## 添加新领域

```bash
# 1. 创建领域结构（需包含 domain.json）
mkdir -p domains/my-category/my-domain/{rules,agents,commands,mcp,skills}

# 2. 创建领域元数据
cat > domains/my-category/my-domain/domain.json << 'EOF'
{
  "name": "my-domain",
  "description": "My custom domain configuration",
  "version": "1.0.0",
  "tags": ["custom"],
  "dependencies": []
}
EOF

# 3. 添加规则、技能等内容
echo "## My Domain Rules" > domains/my-category/my-domain/rules/my-domain.md

# 4. 提交
git add domains/my-category/ && git commit -m "feat: add my-domain configs" && git push
```

## CLI 命令

| 命令 | 功能 |
|------|------|
| `list` | 列出所有可用领域 |
| `status` | 显示当前项目激活的领域 |
| `info <domain>` | 显示领域元数据 |
| `activate <d...>` | 激活一个或多个领域 |
| `deactivate <d...>` | 停用一个或多个领域 |
| `use-stack <name>` | 使用预设堆栈激活多个领域 |
| `sync` | 刷新 Core + 所有激活领域 |

## 工具管理

所有工具集中在仓库根部的 `tools/` 目录，不在各领域 skill 中重复存放。

`vibe-stack sync` 会自动扫描 `tools/` 下所有包含 `pyproject.toml` 的工具目录，生成 `~/.config/opencode/rules/vibe-stack-tools.md` 规则文件。AI 智能体启动时自动加载该文件，通过其中的绝对路径定位工具。

### 添加新工具

```bash
# 放入工具代码
cp -r my-tool tools/

# 执行 sync 生成工具索引
vibe-stack sync
```

### Skill 引用方式

Skill 的 `SKILL.md` 通过引用 `vibe-stack-tools.md` 中的路径执行工具——不捆绑工具代码：

```markdown
工具位于 Vibe Stack 仓库的 `tools/my-tool/`，具体路径见
`~/.config/opencode/rules/vibe-stack-tools.md`。

使用：uv run --project <VIBE_STACK_ROOT>/tools/my-tool <command>
```

## 架构原则

- **仅依赖 OpenCode** — 不依赖 OhMyOpenAgent 或其他插件，配置目标只有 `opencode.json`
- **文件拷贝替代符号链接** — 源文件变更后需显式 `vibe-stack sync` 才会传播，避免意外变更
- **命名空间子目录替代文件名前缀** — 保持原始文件名，删除干净，项目内容不受影响
- **状态文件追踪所有权** — `.vibe-stack-state.json` 记录所有 vibe-stack 管理的文件，停用时精确删除
- **domain.json 标记领域根** — `domains/**/domain.json` 递归发现，支持任意深度嵌套
- **一切 Git 版本化** — 所有配置都在此仓库中追踪
- **模型无关** — 智能体的模型参数不在本仓库范围内（由用户按机器配置）
- **Python/uv 驱动的 CLI** — 使用 Python 3.11+ 编写，通过 uv 管理虚拟环境

## MCP 配置

MCP 路径解析采用轻量级的环境变量 + 配置文件机制：

### 解析优先级（从高到低）

1. `MCP_PATH_{SERVER_NAME}` 环境变量
2. `MCP_PATH` 环境变量（通用回退）
3. `~/.config/opencode/vibe-mcp-paths.json` 配置文件
4. 命令字符串原样（依赖系统 PATH）

### vibe-mcp-paths.json 格式

```jsonc
// ~/.config/opencode/vibe-mcp-paths.json
{
  "data-forge": "C:\\tools\\data-forge.exe",
  "codebase-memory": "/usr/local/bin/codebase-memory-mcp"
}
```

### 领域 MCP 声明

领域通过 `mcp/*.json` 声明 MCP 服务器，使用 `${VARNAME}` 占位符引用可执行路径：

```jsonc
// domains/ai/data-forge/mcp/data-forge.json
{
  "mcpServers": {
    "data-forge": {
      "type": "local",
      "command": ["${MCP_PATH_DATA_FORGE}", "--port=8080"],
      "enabled": true
    }
  }
}
```

激活领域时，`vibe-stack` 自动解析占位符，将解析后的 MCP 配置写入 `.opencode/opencode.json`（以 `vibe:` 前缀区分）。

## 环境要求

- OpenCode >= 1.15.x（推荐最新版本）
- Python >= 3.11
- uv（Python 包管理器，安装方式：https://docs.astral.sh/uv）
- Git

## 安装（3 步）

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/opencode-vibe-stack.git ~/.opencode-vibe-stack

# 2. 安装 Python 依赖
cd ~/.opencode-vibe-stack && uv sync

# 3. 初次同步（Core → ~/.config/opencode/）
uv run vibe-stack sync
```

`sync` 命令会将 core/ 下的配置拷贝到 `~/.config/opencode/`，并写入必要的 `opencode.json` 条目。

## 许可证

MIT
