---
name: custom-mcp
description: 当用户需要创建或管理 OpenCode MCP 服务器配置时使用
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

本地 MCP 服务器采用**自包含模式**：一个 JSON 声明文件加上一个同名的伴随文件夹。JSON 文件声明 MCP 的启动参数，伴随文件夹包含 MCP 项目的代码或二进制文件。使用 `${MCP_LINK_DIR}` 占位符在 JSON 中引用伴随文件夹的路径，激活时自动解析为绝对路径。

远程 MCP 服务器只需要一个 JSON 声明文件，自包含 `type: "remote"` 和 `url` 信息。

---

## 2. 部署位置

### 确定添加内容的位置

当用户描述添加内容时，按以下规则确定存放位置的层级：

- **"添加常驻内容"** 或类似描述 → `core/` 目录（全局常驻配置）
- **"为 xxx domain" / "xxx 领域" / "为 xxx 添加内容"** 或类似描述 → `domains/<category>/<domain>/` 目录（领域专属配置）
- **"为当前项目添加内容"** 或类似描述 → `.opencode/` 目录（项目专属配置）
- **"为本地用户配置" / "为本地用户"** 或类似描述 → `~/.config/opencode/` 目录（用户本地配置）
- **未明确指明位置** → **必须询问用户**具体的添加位置，绝对不允许擅自做决策

### 2.1 全局 MCP（全局可用）
全局 MCP 服务器配置放置在 `core/mcp/` 目录下。

远程 MCP — 仅需一个 JSON 声明文件：
```
core/mcp/
  └── <server-name>.json           # MCP 声明文件（type: "remote" + url）
```

本地 MCP — JSON 声明文件 + 同名伴随文件夹：
```
core/mcp/
  ├── <server-name>.json           # MCP 声明文件（使用 ${MCP_LINK_DIR} 占位符）
  └── <server-name>/               # 伴随文件夹，包含 MCP 项目代码或二进制文件
```

### 2.2 领域 MCP（领域专用）

领域 MCP 服务器配置放置在所属领域的 `mcp/` 目录下。

远程 MCP：
```
domains/<category>/<domain>/
  mcp/
    └── <server-name>.json           # MCP 声明文件（type: "remote" + url）
```

本地 MCP：
```
domains/<category>/<domain>/
  mcp/
    ├── <server-name>.json           # MCP 声明文件（含 ${MCP_LINK_DIR} 占位符）
    └── <server-name>/               # 伴随文件夹，包含 MCP 项目代码或二进制文件
```

### 2.3 项目 MCP（项目专用）
项目 MCP 服务器配置放置在 `.opencode/mcp/` 目录下。

远程 MCP：
```
.opencode/mcp/
  └── <server-name>.json           # MCP 声明文件（type: "remote" + url）
```

本地 MCP：
```
.opencode/mcp/
  ├── <server-name>.json           # MCP 声明文件（含 ${MCP_LINK_DIR} 占位符）
  └── <server-name>/               # 伴随文件夹，包含 MCP 项目代码或二进制文件
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

vibe-stack 使用**自包含模式**管理 MCP 服务器配置，不再依赖外部注册表。
每个 MCP 服务器的 JSON 声明文件包含完整的启动信息，无需额外配置步骤。

### 6.1 激活流程

当执行 `vibe-stack activate <domain>` 时：

1. **扫描 JSON 声明文件** — 读取领域中所有 `mcp/*.json` 文件
2. **检测伴随文件夹** — 若 JSON 文件存在同名的伴随文件夹（`mcp/{name}/`），则为本地 MCP；否则为远程 MCP
3. **远程 MCP** — 直接读取 JSON 中的 `type: "remote"` 和 `url`，写入目标配置文件
4. **本地 MCP** — 将伴随文件夹链接到 `.opencode/mcp/{prefix}_{name}/`，解析 JSON 中的 `${MCP_LINK_DIR}` 占位符为链接后的绝对路径，将解析后的配置写入目标配置文件
5. **添加命名空间前缀** — 为服务器名称添加 `vibe:` 前缀（Core MCP 使用 `vibe:core-`，Domain MCP 使用 `vibe:`）
6. **写入配置文件** — Core MCP 写入 `~/.config/opencode/opencode.json`，Domain MCP 写入 `.opencode/opencode.json`
7. OpenCode 启动时自动发现并连接

### 6.2 `${MCP_LINK_DIR}` 占位符

本地 MCP 的 JSON 声明文件中使用 `${MCP_LINK_DIR}` 占位符引用伴随文件夹的路径：

```json
{
  "mcp": {
    "my-local-server": {
      "type": "local",
      "command": ["${MCP_LINK_DIR}/start.sh"],
      "cwd": "${MCP_LINK_DIR}",
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

激活时，`${MCP_LINK_DIR}` 自动解析为伴随文件夹链接后的绝对路径：

- **Core MCP**: `~/.config/opencode/mcp/{name}/`
- **Domain MCP**: `.opencode/mcp/{category}_{domain}_{name}/`

### 6.3 远程 MCP 配置示例

远程 MCP 无需伴随文件夹，JSON 声明文件自包含所有信息：

```json
{
  "mcp": {
    "my-remote-server": {
      "type": "remote",
      "url": "https://mcp.example.com/mcp",
      "enabled": true
    }
  }
}
```

### 6.4 本地 MCP 配置示例

本地 MCP 需要 JSON 声明文件 + 同名伴随文件夹：

```
domains/<category>/<domain>/
  mcp/
    ├── my-local-server.json       # MCP 声明文件
    └── my-local-server/           # 伴随文件夹
        ├── start.sh               # 启动脚本
        ├── my-binary.exe          # 可执行文件
        └── config.yaml            # 配置文件
```

JSON 声明文件内容：

```json
{
  "mcp": {
    "my-local-server": {
      "type": "local",
      "command": ["${MCP_LINK_DIR}/my-binary.exe", "--serve", "--mcp"],
      "cwd": "${MCP_LINK_DIR}",
      "enabled": true
    }
  }
}
```

### 6.5 Core MCP vs Domain MCP

| 类型 | 配置文件位置 | 命名空间前缀 |
|------|-------------|-------------|
| **Core MCP** | `~/.config/opencode/opencode.json` | `vibe:core-` |
| **Domain MCP** | `.opencode/opencode.json` | `vibe:` |

- **Core MCP** — 影响所有项目，在 vibe-stack 安装时自动激活
- **Domain MCP** — 仅影响激活了该领域的项目，随领域激活/停用

---

## 7. 创建 MCP 服务器的完整流程

```bash
# 1. 确定 MCP 类型和作用范围
# 全局（Core）MCP → core/mcp/
# 领域 MCP → domains/<category>/<domain>/mcp/
# 项目 MCP → .opencode/mcp/

# 2. 创建 MCP 声明 JSON 文件
# 使用 OpenCode 原生 mcp 格式
# 远程 MCP：mcp/<name>.json（自包含 type: "remote" 和 url）
# 本地 MCP：mcp/<name>.json + mcp/<name>/（伴随文件夹）

# 3. 对于本地 MCP，准备伴随文件夹
# 将 MCP 项目代码、二进制文件或脚本放在 mcp/<name>/ 下
# 在 JSON 中使用 ${MCP_LINK_DIR} 占位符引用路径

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
