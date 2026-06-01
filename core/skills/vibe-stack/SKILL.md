# Vibe Stack - 领域配置管理器

管理 AI 智能体工具链的领域特定配置。

## 概述

Vibe Stack 为 OpenCode + OhMyOpenAgent (OMO) 提供分层配置系统。
它按领域隔离规则、智能体、MCP、命令和技能（例如 Unity、Unreal、Blender）。

领域配置存储在一个中央 Git 仓库中，并通过符号链接按项目激活。

## 关键位置

| 路径 | 用途 |
|------|---------|
| `~/.opencode-vibe-stack/core/` | 始终加载的常驻配置 |
| `~/.opencode-vibe-stack/domains/<category>/<domain>/` | 领域特定配置 |
| `~/.opencode-vibe-stack/stacks/` | 预设领域组合 |
| `~/.config/opencode/` | 用户级配置（符号链接到 core/） |
| `.opencode/` | 项目级配置（符号链接到 domains/） |

## 使用命令

当你需要管理领域配置时，使用 `vibe-stack` CLI：

```bash
# List all available domains
vibe-stack list

# Show active domains in current project
vibe-stack status

# Activate a domain for the current project
vibe-stack activate game-dev/unity

# Deactivate a domain
vibe-stack deactivate game-dev/unity

# Activate a preset stack
vibe-stack use-stack game-dev
```

## 添加新领域

1. 创建目录：`domains/<category>/<domain>/`
2. 添加必要的子目录：`rules/`、`agents/`、`commands/`、`mcp/`、`skills/`
3. 配置领域特定的规则、智能体等
4. 提交并推送到仓库

## 配置分层

当打开项目时，按以下顺序加载配置：
1. **核心**（始终加载）- 来自 `~/.config/opencode/`（符号链接到 core/）
2. **项目** - 来自项目根目录的 `.opencode/`
3. **领域** - 来自 `vibe-stack activate` 创建的符号链接

OMO 的原生配置遍历（从 `.opencode/` 到 `$HOME`）会自动处理合并。

## MCP 服务器管理

领域 MCP 服务器 **仅在领域被激活时** 加载 —— 无全局 MCP 杂乱。

### 工作原理

1. 每个领域的 `mcp/` 目录包含一个或多个 OpenCode 原生格式的 JSON 定义文件
2. 执行 `vibe-stack activate` 时，CLI：
   - 读取领域中所有 `mcp/*.json` 文件
   - 解析 `${VIBE_STACK_HOME}` 和 `${PROJECT_ROOT}` 占位符
   - 为服务器名称添加 `vibe:` 命名空间前缀（例如 `vibe:data-forge`）
   - 将条目合并到 `.opencode/opencode.json` 的 `mcp` 键下
3. OpenCode 在启动时自动发现 `.opencode/opencode.json` 并连接到 MCP 服务器
4. 执行 `vibe-stack deactivate` 时，`vibe:*` 条目被移除

### MCP 定义格式

在领域定义文件中使用 OpenCode 原生 `mcp` 格式：

```json
{
  "mcp": {
    "server-name": {
      "type": "local",
      "command": ["python", "${VIBE_STACK_HOME}/domains/my-cat/my-domain/mcp/my-server/server.py"],
      "enabled": true,
      "environment": {
        "MY_VAR": "${PROJECT_ROOT}/data"
      }
    }
  }
}
```

### 目录结构

```
domains/<category>/<domain>/
  mcp/
    my-server.json       # MCP definition (OpenCode format)
    my-server/           # MCP server project code (optional)
      pyproject.toml
      src/server.py
```

### 关键规则

- **不修改用户配置** —— 所有 MCP 配置写入 `.opencode/opencode.json`（项目级）
- **命名空间隔离** —— `vibe:` 前缀防止与用户/Claude Code MCP 冲突
- **占位符解析** —— `${VIBE_STACK_HOME}` 和 `${PROJECT_ROOT}` 在激活时解析
- **按领域生命周期** —— MCP 随其领域一起激活/停用
