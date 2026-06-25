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

创建和管理以 OpenCode 技能（Skill）形式封装的本地自定义 MCP 服务器。Skill-MCP 是一个自包含的技能目录，内含 MCP 服务器项目代码、启动配置和技能描述。技能加载时，oh-my-openagent 自动启动嵌入的 MCP 服务器，会话结束时自动清理。

---

## 1. 创建规范

### 目录结构

```
<skill-name>/
  ├── SKILL.md              # 技能描述文件（必需 + YAML frontmatter）
  ├── mcp.json              # MCP 启动配置（可选，优先级高于 frontmatter）
  └── <mcp-project>/        # MCP 项目代码（必需）
      ├── pyproject.toml    # Python | package.json  # Node.js | Cargo.toml # Rust
      └── src/
```

每个文件的职责：

| 文件/目录 | 必需 | 说明 |
|-----------|------|------|
| `SKILL.md` | 是 | 技能描述，含 YAML frontmatter。可选的 `mcp:` 字段声明 MCP 配置 |
| `mcp.json` | 否 | MCP 启动配置。存在时**优先于** SKILL.md frontmatter |
| `<mcp-project>/` | 是 | MCP 服务器项目代码。支持源码项目、git submodule、预构建二进制 |

### MCP 配置格式

两种方式，**mcp.json 优先**。

**方式 A：SKILL.md YAML frontmatter（简化格式）**

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

**方式 B：mcp.json（推荐）**

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

也支持无 `mcpServers` 包裹的扁平格式，以及 HTTP 远程 MCP：

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

**配置字段**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `command` | string / array | 是（local） | 启动命令。数组形式：`["uv", "run", "xxx"]` |
| `args` | string[] | 否 | 命令参数数组，与 command 合并 |
| `type` | string | 否 | `"local"`（默认）或 `"remote"` |
| `url` | string | 是（remote） | 远程 MCP 服务器 URL |
| `cwd` | string | 否 | 工作目录。相对于技能目录的路径，如 `"./my-mcp-project"` |
| `timeout` | number | 否 | 超时（毫秒），默认 5000 |
| `env` | object | 否 | 环境变量键值对 |

---

## 2. 放置规则

Skill-MCP 的放置位置决定作用范围。

### 三级放置

| 层级 | 路径 | 作用范围 | 使用场景 |
|------|------|---------|---------|
| 领域专属 | `domains/{category}/{domain}/skills/{mcp-name}/` | 该领域激活时可用 | 领域专属工具 |
| 全局常驻 | `core/skills/{mcp-name}/` | 全局始终可用 | 通用基础设施工具（慎用） |
| 项目专属 | `.opencode/skills/{mcp-name}/` | 仅当前项目 | 项目特定的自定义集成 |

### 放置决策链

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

---

## 3. 边界规则：custom-skill-mcp vs custom-mcp

### 何时用哪个

| 条件 | 用 |
|------|----|
| **自己开发的**自定义 MCP，项目代码在本地 | custom-skill-mcp |
| **第三方** MCP 工具（SaaS、npm 包、预构建二进制） | custom-mcp |
| 只需要在 opencode.json 加一行注册 | custom-mcp |

### 决策流程

```
需要添加 MCP 工具
    ↓
这个 MCP 是自己开发的吗？
    +-- 是 → custom-skill-mcp（MCP 代码放技能目录内，mcp.json 配置启动）
    +-- 否 → custom-mcp（配置在 opencode.json 或领域 mcp/ 目录）
```

### 约束

- 一个 MCP 只能使用**一种**激活机制。已在 opencode.json 注册的，不应再封装为 Skill-MCP，反之亦然。
- Skill-MCP 要求 MCP 项目代码**自包含**在技能目录内。外部仓库应先作为 git submodule 或复制进来。
- 不要为已有全局注册方案的第三方 MCP 创建 Skill-MCP 封装。

---

## 4. 规则集

### 命名规则

- 技能名称与 MCP 服务器名称保持一致
- 技能目录名与 frontmatter 的 `name` 字段一致
- 正则约束：`^[a-z0-9]+(-[a-z0-9]+)*$`
- 推荐格式：`{功能描述}-mcp`，如 `unity-mcp`

### 代码自包含规则

- MCP 项目代码必须完全自包含在技能目录中
- 使用 `uv`（Python）、`bun`（JS/TS）、`cargo`（Rust）管理依赖
- 避免依赖全局安装的运行时或包
- 大型 MCP 项目使用 git submodule

### 配置规则

- 优先使用 `mcp.json` 而非 SKILL.md frontmatter
- 敏感信息（API 密钥等）通过 `env` 字段引用环境变量，使用 `{env:VAR_NAME}` 语法，禁止硬编码
- 长时间运行任务设置合理的 `timeout`
- 配置优先级：mcp.json > SKILL.md frontmatter `mcp:` > 无 MCP 配置

### 跨平台规则

- MCP 启动命令需兼容 Windows、Linux、macOS
- Python 项目统一 `uv run`，Node.js 项目统一 `bun run`
- 禁止使用平台特定的路径分隔符或 shell 语法
- 平台特定配置在 `mcp.json` 中分别处理

### 生命周期规则

- MCP 服务器跟随智能体会话自动启动和销毁
- 禁止在技能中实现全局状态或持久连接
- 每个会话使用独立的 MCP 实例
- 禁止在 MCP 中创建后台守护进程

### 工具命名规则

- 工具名包含业务语义，如 `unity_execute_code` 而非 `exec`
- 工具描述清晰说明功能、参数和返回值
- 避免创建过多细粒度工具，一个工具完成一个有意义的操作单元
- 工具参数使用明确的类型定义

### 测试规则

- 创建后通过加载技能并调用其工具进行验证
- 验证 MCP 服务器在会话结束时正确清理
- 确保工具描述清晰、参数完整
- 测试 MCP 不可用时的降级行为

---

## 示例：hn-unity-mcp

目录结构：

```
domains/game-dev/unity/skills/hn-unity-mcp/
  ├── SKILL.md              # 技能描述
  ├── mcp.json              # MCP 启动配置
  └── HNUnityMCP/           # Python MCP 项目（git submodule）
      ├── pyproject.toml
      └── src/hn_unity_mcp/
```

SKILL.md：

```yaml
---
name: hn-unity-mcp
description: 当用户需要通过 MCP 工具与 Unity Editor 进行实时交互时使用
license: MIT
compatibility: opencode
---

# hn-unity-mcp — Unity Editor MCP 集成

## 工具列表
- `unity_execute_code`: 在 Unity Editor 中执行 C# 代码
- `unity_get_scene_info`: 获取当前场景信息
- `unity_find_objects`: 查找场景中的 GameObject
- `unity_manage_assets`: 管理项目资源
```

mcp.json：

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

---

## 使用时机速查

| 场景 | 使用技能 |
|------|---------|
| 用 Python 写一个文件操作 MCP 工具 | custom-skill-mcp |
| 集成 GitHub 官方的 MCP 服务 | custom-mcp |
| 为 Unity 编辑器写一个通信 MCP | custom-skill-mcp |
| 配置 Sentry MCP 监控应用 | custom-mcp |
| 把已有的 Python 脚本封装成 MCP 工具 | custom-skill-mcp |
| 用 npm 安装 `@modelcontextprotocol/server-filesystem` | custom-mcp |
