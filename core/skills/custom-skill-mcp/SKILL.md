---
name: custom-skill-mcp
description: 当用户需要创建或管理以技能形式封装的本地自定义 MCP 服务器时使用。每个自定义 MCP 作为一个独立技能存在，MCP 项目文件放置在技能文件夹内。
license: MIT
compatibility: opencode
metadata:
  audience: contributors
  category: domain-config
---

# custom-skill-mcp — 以技能形式封装的自定义 MCP 开发指南

指导你创建和管理以 OpenCode 技能（Skill）形式封装的本地自定义 MCP 服务器。每个 Skill-MCP 是一个自包含的技能目录，其中包含 MCP 服务器项目代码、启动配置和技能描述。当技能被加载时，其嵌入的 MCP 服务器由 oh-my-openagent 自动启动，会话结束时自动清理。

---

## 1. Skill-MCP 概述

### 什么是 Skill-MCP

Skill-MCP 是将 MCP（Model Context Protocol）服务器封装为 OpenCode 技能的一种开发模式。它把 MCP 服务器的项目代码、启动配置和技能描述统一放在一个技能目录中，使得 MCP 工具的开发、分发和使用完全自包含。

### 工作流程

1. 技能目录包含 SKILL.md（技能描述 + 可选 MCP 配置）和 MCP 项目代码
2. 当智能体加载该技能时，oh-my-openagent 自动读取 MCP 配置并启动 MCP 服务器
3. MCP 工具在会话期间可用，智能体可以调用这些工具
4. 会话结束时，MCP 服务器进程自动清理

### Skill-MCP vs 传统 MCP 对比

| 特性 | 传统 MCP（opencode.json） | Skill-MCP（技能嵌入） |
|------|--------------------------|----------------------|
| 配置位置 | opencode.json 的 mcp 字段 | 技能目录内的 SKILL.md 或 mcp.json |
| 代码归属 | 外部项目 / npm 包 / 二进制 | 自包含在技能目录内 |
| 分发方式 | 独立安装 | 随技能目录分发 |
| 调用方式 | 始终可用（全局注册） | 按需加载（智能体加载技能时启动） |
| 生命周期 | 跟随 OpenCode 进程 | 跟随智能体会话 |
| 适用场景 | 第三方工具、长期运行服务 | 自研自定义工具、项目专属工具 |
| 版本管理 | 独立于技能体系 | 与技能版本绑定 |

### 核心优势

- **自包含**：MCP 代码、配置和技能描述打包在一起，无需额外安装
- **按需启动**：只在技能被加载时启动 MCP 服务器，节省资源
- **会话级生命周期**：不会在多个会话间残留进程
- **易于分发**：整个技能目录即可完成分发，无需单独配置 opencode.json

---

## 2. 边界定义：custom-skill-mcp vs custom-mcp

### 两个命令的职责划分

| 维度 | custom-skill-mcp | custom-mcp |
|------|-----------------|------------|
| 目标 MCP | **自己开发的**自定义 MCP | **第三方** MCP 工具 |
| MCP 来源 | 本地开发的项目代码 | SaaS 服务、npm 包、预构建二进制 |
| 代码管理 | MCP 项目代码放在技能目录内 | 不需要管理代码，仅配置连接 |
| 典型场景 | 项目专属工具、自研集成工具 | GitHub MCP、Sentry MCP、Context7 |
| 配置方式 | mcp.json 或 SKILL.md frontmatter | opencode.json 的 mcp 字段 |

### 决策流程

```
需要添加一个 MCP 工具
    |
    v
这个 MCP 是自己开发的吗？
    |
    +-- 是 --> 使用 custom-skill-mcp（本技能）
    |             将 MCP 项目代码放在技能目录内
    |             通过 mcp.json 配置启动
    |
    +-- 否 --> 使用 custom-mcp
                  配置在 opencode.json 或领域 mcp/ 目录
                  引用外部二进制 / npm 包 / 远程 URL
```

### 关键约束

- 一个 MCP 只能使用**一种**激活机制。如果已在 opencode.json 中注册，不应再封装为 Skill-MCP，反之亦然。
- Skill-MCP 要求 MCP 项目代码**自包含**在技能目录内。如果 MCP 代码是外部仓库，应先将其作为 git submodule 或复制到技能目录中。
- 不要为已有全局注册方案的第三方 MCP 创建 Skill-MCP 封装。

---

## 3. 目录结构模板

### 标准结构

```
<skill-name>/
  ├── SKILL.md              # 技能描述文件（必需）
  ├── mcp.json              # MCP 启动配置（优先级高于 frontmatter）
  └── <mcp-project>/        # MCP 项目代码目录
      ├── pyproject.toml    # 示例：Python 项目
      ├── package.json      # 示例：Node.js 项目
      ├── Cargo.toml        # 示例：Rust 项目
      └── src/              # 源代码
```

### 各文件说明

| 文件/目录 | 必需 | 说明 |
|-----------|------|------|
| `SKILL.md` | 是 | 技能描述，包含 YAML frontmatter。可选的 `mcp:` 字段用于 MCP 配置 |
| `mcp.json` | 否 | MCP 启动配置。如果存在，**优先于** SKILL.md 中的 frontmatter 配置 |
| `<mcp-project>/` | 是 | MCP 服务器的项目代码。具体名称和结构取决于技术栈 |

### 支持的 MCP 项目形态

- **源码项目**：Python（pyproject.toml）、Node.js（package.json）、Rust（Cargo.toml）等
- **git submodule**：将外部仓库作为 submodule 引入
- **预构建二进制**：直接放置编译好的可执行文件

---

## 4. MCP 配置格式

Skill-MCP 支持两种 MCP 配置方式：**SKILL.md frontmatter** 和 **mcp.json 文件**。当两者同时存在时，mcp.json 优先。

### 格式 A：SKILL.md YAML frontmatter（简化格式）

适用于简单的 MCP 启动配置，直接在 SKILL.md 的 frontmatter 中声明：

```yaml
---
name: my-custom-mcp
description: 当用户需要执行 XXX 操作时使用
license: MIT
compatibility: opencode
mcp:
  my-custom-mcp:
    type: local
    command:
      - uv
      - run
      - my-custom-mcp
    cwd: ./
    timeout: 30000
---
```

### 格式 B：mcp.json 文件（推荐，优先级更高）

适用于复杂的 MCP 配置，独立于 SKILL.md，便于管理。支持三种子格式：

#### B1. 标准格式（mcpServers 包裹）

```json
{
  "mcpServers": {
    "my-custom-mcp": {
      "command": "uv",
      "args": ["run", "my-custom-mcp"],
      "cwd": "./my-mcp-project",
      "timeout": 60000,
      "env": {
        "MY_ENV_VAR": "value"
      }
    }
  }
}
```

#### B2. 扁平格式（直接定义）

```json
{
  "my-custom-mcp": {
    "command": "uv",
    "args": ["run", "my-custom-mcp"],
    "type": "local",
    "timeout": 30000
  }
}
```

#### B3. HTTP 传输格式（远程 MCP）

```json
{
  "mcpServers": {
    "my-remote-mcp": {
      "type": "remote",
      "url": "http://localhost:8080/mcp",
      "timeout": 5000
    }
  }
}
```

### 配置字段参考

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `command` | string / array | 是（local） | 启动命令。可以是字符串或数组。数组形式：`["uv", "run", "xxx"]` |
| `args` | string[] | 否 | 命令参数数组。与 command 中的参数合并 |
| `type` | string | 否 | `"local"`（默认）或 `"remote"` |
| `url` | string | 是（remote） | 远程 MCP 服务器 URL |
| `cwd` | string | 否 | 工作目录。相对于技能目录的路径，如 `"./my-mcp-project"` |
| `timeout` | number | 否 | 超时时间（毫秒），默认 5000 |
| `env` | object | 否 | 环境变量键值对 |
| `oauth` | object / boolean | 否 | OAuth 配置，用于远程 MCP |

### 配置优先级

1. mcp.json 文件（如果存在）
2. SKILL.md frontmatter 中的 `mcp:` 字段
3. 如果两者都不存在，该技能不启动 MCP 服务器

---

## 5. 技能放置规则

Skill-MCP 技能的放置位置决定其作用范围和优先级。

### 三级放置策略

| 层级 | 路径 | 作用范围 | 使用场景 |
|------|------|---------|---------|
| 领域专属 | `domains/{category}/{domain}/skills/{mcp-name}/` | 该领域激活时可用 | 领域专属工具，如 Unity MCP、AI 数据处理 MCP |
| 全局常驻 | `core/skills/{mcp-name}/` | 全局始终可用 | 通用基础设施工具（慎用） |
| 项目专属 | `.opencode/skills/{mcp-name}/` | 仅当前项目 | 项目特定的自定义集成 |

### 决策优先级

```
1. 该 MCP 是否为某个特定领域服务？
   → 是：放入 domains/{category}/{domain}/skills/
   → 否：继续判断

2. 该 MCP 是否为当前项目专属？
   → 是：放入 .opencode/skills/
   → 否：继续判断

3. 该 MCP 是否为通用基础设施？
   → 是：放入 core/skills/（需要充分理由）
   → 否：重新审视是否需要 Skill-MCP，也许用 custom-mcp 更合适
```

### 领域专属示例

```
domains/game-dev/unity/skills/hn-unity-mcp/     # Unity 编辑器通信 MCP
domains/ai/data-forge/skills/data-processor/     # 数据处理 MCP
domains/web/frontend/skills/component-gen/       # 前端组件生成 MCP
```

### 全局常驻示例（慎用）

```
core/skills/filesystem-ops/    # 文件系统操作 MCP（通用基础设施）
core/skills/shell-executor/    # Shell 命令执行 MCP（通用基础设施）
```

---

## 6. 完整示例 — hn-unity-mcp 结构

以 Unity 游戏开发领域的 `hn-unity-mcp` 为例，展示完整的 Skill-MCP 目录结构。

### 目录结构

```
domains/game-dev/unity/skills/hn-unity-mcp/
  ├── SKILL.md              # 技能描述和 MCP 配置
  ├── mcp.json              # MCP 启动配置（优先）
  └── HNUnityMCP/           # Python MCP 项目代码
      ├── pyproject.toml
      ├── src/
      │   └── hn_unity_mcp/
      │       ├── __init__.py
      │       └── server.py
      └── README.md
```

### SKILL.md 最小示例

```yaml
---
name: hn-unity-mcp
description: 当用户需要通过 MCP 工具与 Unity Editor 进行实时交互，包括执行 C# 脚本、操作场景对象、获取编辑器状态时使用。
license: MIT
compatibility: opencode
---

# hn-unity-mcp — Unity Editor MCP 集成

## 概述

通过 MCP 协议与 Unity Editor 实时通信，提供场景操作、脚本执行、资源管理等功能。

## 使用要求

- Unity Editor 已打开目标项目
- MCP Bridge 已在 Unity 侧配置

## 工具列表

- `unity_execute_code`: 在 Unity Editor 中执行 C# 代码
- `unity_get_scene_info`: 获取当前场景信息
- `unity_find_objects`: 查找场景中的 GameObject
- `unity_manage_assets`: 管理项目资源

## 使用时机

当智能体需要直接操作 Unity Editor 时加载此技能。
```

### mcp.json 内容示例

```json
{
  "mcpServers": {
    "hn-unity-mcp": {
      "command": "uv",
      "args": ["run", "hn-unity-mcp"],
      "cwd": "./HNUnityMCP",
      "timeout": 120000
    }
  }
}
```

### 关键设计要点

- `cwd` 设置为 `"./HNUnityMCP"`，指向 MCP 项目目录
- `uv run` 利用 Python 虚拟环境管理，无需全局安装依赖
- `timeout` 设置为 120 秒，适应 Unity Editor 的响应延迟
- 技能名称 `hn-unity-mcp` 与 MCP 服务器名称一致

---

## 7. 最佳实践

### 命名一致性

- 技能名称应与 MCP 服务器名称保持一致
- 技能目录名与 frontmatter 中的 `name` 字段一致
- 命名遵循 `^[a-z0-9]+(-[a-z0-9]+)*$` 正则规范
- 推荐命名格式：`{功能描述}-mcp`，如 `unity-mcp`、`data-processor-mcp`

### 代码自包含

- MCP 项目代码应完全自包含在技能目录中
- 使用 `uv`（Python）、`bun`（JavaScript/TypeScript）、`cargo`（Rust）管理依赖
- 避免依赖全局安装的运行时或包
- 对于大型 MCP 项目，考虑使用 git submodule

### 配置管理

- 优先使用 `mcp.json` 而非 SKILL.md frontmatter 配置 MCP
- 将敏感信息（API 密钥等）通过 `env` 字段引用环境变量，而非硬编码
- 使用 `{env:VAR_NAME}` 语法引用环境变量
- 为长时间运行的任务设置合理的 `timeout` 值

### 跨平台考虑

- MCP 启动命令应考虑 Windows、Linux、macOS 的差异
- Python 项目统一使用 `uv run`，Node.js 项目统一使用 `bun run`
- 避免使用平台特定的路径分隔符或 shell 语法
- 如需平台特定配置，可在 `mcp.json` 中分别定义

### 测试和验证

- 创建技能后，通过加载技能并调用其工具进行测试
- 验证 MCP 服务器在会话结束时是否正确清理
- 确保 MCP 工具的描述清晰、参数完整
- 测试错误场景：MCP 不可用时的降级行为

### 生命周期管理

- MCP 服务器跟随智能体会话自动启动和销毁
- 不要在技能中实现全局状态或持久连接
- 每个会话应使用独立的 MCP 实例
- 避免在 MCP 中创建后台守护进程

### 工具命名与组织

- MCP 工具名应包含业务语义，如 `unity_execute_code` 而非 `exec`
- 工具描述应清晰说明功能、参数和返回值
- 避免创建过多细粒度工具，一个工具应完成一个有意义的操作单元
- 工具参数使用明确的类型定义（string、number、boolean 等）

---

## 8. 使用时机

### 加载本技能（custom-skill-mcp）

- 当需要创建新的自研自定义 MCP 工具，且希望以技能形式封装时
- 当需要为现有自研 MCP 项目创建技能封装时
- 当需要了解 Skill-MCP 的目录结构、配置格式和最佳实践时
- 当需要将已有 MCP 代码从其他位置迁移到技能目录时

### 改用 custom-mcp 的场景

当以下情况时，应使用 custom-mcp 而非本技能：

- 集成第三方 MCP 服务（如 GitHub MCP、Sentry MCP、Context7）
- 使用 npm 生态的 MCP 包（如 `@anthropic/mcp-server-xxx`）
- 添加通过远程 URL 连接的 MCP 服务器
- 配置已有的预构建 MCP 二进制文件（无需管理源码）
- 只需要在 opencode.json 中添加 MCP 注册条目即可使用的场景

### 判断速查

| 场景 | 使用技能 |
|------|---------|
| 我要用 Python 写一个文件操作 MCP 工具 | custom-skill-mcp |
| 我要集成 GitHub 官方的 MCP 服务 | custom-mcp |
| 我要为 Unity 编辑器写一个通信 MCP | custom-skill-mcp |
| 我要配置 Sentry MCP 监控我的应用 | custom-mcp |
| 我要把一个已有的 Python 脚本封装成 MCP 工具 | custom-skill-mcp |
| 我要用 npm 安装 `@modelcontextprotocol/server-filesystem` | custom-mcp |
