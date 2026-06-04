---
name: custom-mcp
description: 创建 OpenCode MCP 服务器配置的制作规范和完整指南
license: MIT
compatibility: opencode
metadata:
  audience: contributors
  category: configuration
---

# Custom MCP — MCP 服务器制作指南

指导你创建和管理 MCP (Model Context Protocol) 服务器配置。MCP 为 OpenCode 添加外部工具，支持本地和远程两种连接方式。

---

## 1. MCP 概述

MCP (Model Context Protocol) 允许为 OpenCode 添加外部工具。添加后，MCP 工具会自动与内置工具一起提供给 LLM 使用。

> **注意**：MCP 服务器会占用上下文空间，请谨慎选择启用哪些服务器。某些 MCP 服务器（如 GitHub MCP）消耗较大，容易超出上下文限制。

OpenCode 支持两种 MCP 服务器类型：

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **本地 (local)** | 通过本地命令启动 | 本地运行的工具、脚本 |
| **远程 (remote)** | 通过 URL 连接 | SaaS 服务、API 网关 |

本地 MCP 服务器一律使用二进制文件，且需要同时考虑windows和linux平台，避免运行时依赖问题。

---

## 2. 部署位置

### 2.1 全局 MCP（全局可用）
全局 MCP 服务器配置放置在项目根目录的 `.opencode/mcp/` 目录下。

```
.opencode/mcp/
  ├── <server-name>.json           # MCP 注册配置文件（OpenCode 原生格式）
  ├── <server-name>-win.exe        # windows预构建二进制文件
  ├── <server-name>-linux          # linux预构建二进制文件
```

### 2.2 领域 MCP（领域专用）

领域 MCP 服务器配置放置在所属领域的 `mcp/` 目录下。

```
domains/<category>/<domain>/
  mcp/
    ├── <server-name>.json           # MCP 注册配置文件（OpenCode 原生格式）
    ├── <server-name>-win.exe        # windows预构建二进制文件
    ├── <server-name>-linux          # linux预构建二进制文件
```

### 2.3 项目 MCP（项目专用）
项目 MCP 服务器配置放置在 `.opencode/mcp/` 目录下。
```
.opencode/mcp/
  ├── <server-name>.json           # MCP 注册配置文件（OpenCode 原生格式）
  ├── <server-name>-win.exe        # windows预构建二进制文件
  ├── <server-name>-linux          # linux预构建二进制文件
```
---

## 3. MCP 定义格式

### 3.1 本地 MCP

```json
{
  "mcp": {
    "server-name": {
      "type": "local",
      "command": ["npx", "-y", "my-mcp-command"],
      "enabled": true,
      "environment": {
        "MY_ENV_VAR": "my_value"
      },
      "timeout": 5000
    }
  }
}
```

| 选项 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `type` | string | **是** | 必须为 `"local"` |
| `command` | array | **是** | 启动命令及参数数组 |
| `enabled` | boolean | 否 | 启用状态，默认禁用 |
| `environment` | object | 否 | 运行时环境变量 |
| `timeout` | number | 否 | 超时时间（毫秒），默认 5000 |

### 3.2 远程 MCP

```json
{
  "mcp": {
    "server-name": {
      "type": "remote",
      "url": "https://my-mcp-server.com",
      "enabled": true,
      "headers": {
        "Authorization": "Bearer MY_API_KEY"
      },
      "timeout": 5000
    }
  }
}
```

| 选项 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `type` | string | **是** | 必须为 `"remote"` |
| `url` | string | **是** | 远程服务器 URL |
| `enabled` | boolean | 否 | 启用状态 |
| `headers` | object | 否 | 请求头 |
| `oauth` | object | 否 | OAuth 配置（详见下文） |
| `timeout` | number | 否 | 超时时间（毫秒），默认 5000 |

---

## 4. OAuth 认证

OpenCode 自动处理远程 MCP 服务器的 OAuth 认证：

### 自动认证

大多数支持 OAuth 的 MCP 服务器无需特殊配置：

```json
{
  "mcp": {
    "my-oauth-server": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

首次使用时 OpenCode 会提示认证。也可手动触发：

```bash
opencode mcp auth my-oauth-server
```

### 预注册凭据

```json
{
  "mcp": {
    "my-oauth-server": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp",
      "oauth": {
        "clientId": "{env:MY_CLIENT_ID}",
        "clientSecret": "{env:MY_CLIENT_SECRET}",
        "scope": "tools:read tools:execute"
      }
    }
  }
}
```

### 禁用 OAuth

```json
{
  "mcp": {
    "my-api-key-server": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp",
      "oauth": false,
      "headers": {
        "Authorization": "Bearer {env:MY_API_KEY}"
      }
    }
  }
}
```

### 认证管理命令

```bash
opencode mcp auth <server-name>        # 认证
opencode mcp list                       # 列出所有 MCP 及认证状态
opencode mcp logout <server-name>      # 注销
opencode mcp debug <server-name>       # 调试连接和 OAuth 流程
```

---

## 5. MCP 工具管理

### 5.1 全局禁用

```json
{
  "tools": {
    "my-mcp-server_*": false
  }
}
```

### 5.2 按代理控制

```json
{
  "tools": {
    "my-mcp*": false
  },
  "agent": {
    "my-agent": {
      "tools": {
        "my-mcp*": true
      }
    }
  }
}
```

### 5.3 Glob 模式说明

- `*` 匹配零个或多个任意字符
- `?` 匹配恰好一个字符
- MCP 工具注册时以服务器名称为前缀，如 `my-server_toolname`

---

## 6. vibe-stack 的 MCP 管理机制

### 6.1 激活流程

当执行 `vibe-stack activate <domain>` 时：

1. 读取领域中所有 `mcp/*.json` 文件
2. 解析 `${VIBE_STACK_HOME}` 和 `${PROJECT_ROOT}` 占位符
3. 为服务器名称添加 `vibe:` 命名空间前缀（如 `vibe:data-forge`）
4. 将条目合并到 `.opencode/opencode.json` 的 `mcp` 键下
5. OpenCode 启动时自动发现并连接

### 6.2 占位符解析

```json
{
  "mcp": {
    "data-forge": {
      "type": "local",
      "command": [
        "${VIBE_STACK_HOME}/domains/ai/data_forge/mcp/data-forge.exe"
      ],
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

- `${VIBE_STACK_HOME}` — 解析为 vibe-stack 仓库根目录
- `${PROJECT_ROOT}` — 解析为当前项目根目录

### 6.3 二进制发布支持

MCP 服务器推荐使用预构建二进制文件，避免项目中需要 Python/Node 运行时：

```json
{
  "mcp": {
    "data-forge": {
      "type": "local",
      "command": [
        "${VIBE_STACK_HOME}/domains/ai/data_forge/mcp/data-forge.exe"
      ],
      "enabled": true,
      "release": {
        "repo": "owner/repo-name",
        "asset": {
          "linux": "binary-linux-x64",
          "windows": "binary-windows-x64.exe",
          "darwin": "binary-macos-x64"
        }
      }
    }
  }
}
```

---

## 7. 创建 MCP 服务器的完整流程

```bash
# 1. 确定 MCP 类型和作用范围
# 全局 MCP → .opencode/mcp/
# 领域 MCP → domains/<category>/<domain>/mcp/
# 项目 MCP → .opencode/mcp/

# 2. 创建 MCP 定义 JSON 文件
# 使用 OpenCode 原生 mcp 格式

# 3. 构建或下载 MCP 服务器二进制文件
# 放置在 mcp/ 目录下

# 4. 测试激活
vibe-stack activate <category>/<domain>
vibe-stack status

# 5. 在 OpenCode 中测试
# 输入提示词使用 MCP 工具
```

---

## 8. 最佳实践

- **命名空间隔离**：`vibe:` 前缀防止与用户/Claude Code 的 MCP 冲突
- **领域生命周期**：MCP 随其领域一起激活/停用
- **二进制优先**：MCP 服务器使用预构建二进制文件，无需运行时依赖
- **超时配置**：长时间运行的任务（如数据处理）设置较长的 timeout
- **环境变量**：敏感信息通过 `{env:VAR_NAME}` 引用环境变量，不硬编码
- **组织远程配置**：企业用户可通过 `.well-known/opencode` 端点提供默认 MCP

### 常见 MCP 示例

**Sentry**：
```json
{
  "sentry": {
    "type": "remote",
    "url": "https://mcp.sentry.dev/mcp",
    "oauth": {}
  }
}
```

**Context7 (文档搜索)**：
```json
{
  "context7": {
    "type": "remote",
    "url": "https://mcp.context7.com/mcp"
  }
}
```

**Grep by Vercel (代码搜索)**：
```json
{
  "gh_grep": {
    "type": "remote",
    "url": "https://mcp.grep.app"
  }
}
```
