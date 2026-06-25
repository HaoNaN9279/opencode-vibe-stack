# Bug: `skill_mcp` 调用 hn-unity-mcp 失败 — `cwd` 被忽略

## 问题现象

通过 `skill_mcp` 工具调用 hn-unity-mcp 的 `get_compile_errors` 时失败：

```
skill_mcp(mcp_name="hn-unity-mcp", tool_name="get_compile_errors")
→ Failed to connect to MCP server "hn-unity-mcp".
→ Command: uv run hn-unity-mcp
→ Reason: MCP error -32000: Connection closed
```

但所有底层组件手动测试均正常。

## 架构链路

```
OpenCode AI
  └─ skill_mcp 工具
       └─ oh-my-openagent / SkillMcpManager
            └─ StdioClientTransport (来自 @modelcontextprotocol/sdk)
                 └─ spawn(command, args, { cwd, env, ... })
                      └─ uv run hn-unity-mcp
                           └─ Python MCP Server (hn_unity_mcp.server)
                                └─ HTTP POST → Unity Editor (HNUnityMCP 扩展)
                                     └─ get_compile_errors
```

## 根因

**`oh-my-openagent` 的 `SkillMcpManager.createStdioClient()` 创建 MCP Server 子进程时，没有把 `mcp.json` 中的 `cwd` 配置传递给 `StdioClientTransport`，导致进程在错误的当前工作目录下启动。**

### 代码链路

#### 1. `mcp.json` 中定义了 `cwd`

```json
{
  "mcpServers": {
    "hn-unity-mcp": {
      "command": "uv",
      "args": ["run", "hn-unity-mcp"],
      "cwd": ".opencode/skills/game-dev_unity_hn-unity-mcp/HNUnityMCP/python",
      "timeout": 30000
    }
  }
}
```

`cwd` 指向 Python MCP Server 项目目录，其中包含 `pyproject.toml`，定义了 `hn-unity-mcp` CLI entry point。

#### 2. Skill loader 加载 `mcp.json`

文件: `packages/skills-loader-core/src/features/opencode-skill-loader/skill-mcp-config.ts`

```typescript
export async function loadMcpJsonFromDir(skillDir: string): Promise<SkillMcpConfig | undefined> {
  const mcpJsonPath = join(skillDir, "mcp.json")
  const content = await fs.readFile(mcpJsonPath, "utf-8")
  const parsed = JSON.parse(content) as Record<string, unknown>
  if (parsed && typeof parsed === "object" && "mcpServers" in parsed && parsed.mcpServers) {
    return parsed.mcpServers as SkillMcpConfig  // cwd 在 JS 对象中还存在
  }
}
```

JSON 被完整解析为 JS 对象，此时 `cwd` 属性仍然存在于对象中（JavaScript 不会删除未知属性）。

#### 3. `ClaudeCodeMcpServer` 类型没有 `cwd`

文件: `src/features/claude-code-mcp-loader/types.ts`

```typescript
export interface ClaudeCodeMcpServer {
  type?: "http" | "sse" | "stdio"
  url?: string
  command?: string
  args?: string[]
  env?: Record<string, string>
  headers?: Record<string, string>
  disabled?: boolean
  // ⚠️ 没有 cwd 字段！
}
```

TypeScript 类型定义中**缺失 `cwd?: string`**。虽然运行时对象中 `cwd` 属性还在，但 TypeScript 代码感知不到它，也不会使用它。

#### 4. `createStdioClient` 没有传递 `cwd`

文件: `src/features/skill-mcp-manager/manager.ts`

```typescript
private async createStdioClient(
  info: SkillMcpClientInfo,
  config: ClaudeCodeMcpServer
): Promise<Client> {
  const command = config.command
  const args = config.args || []
  const mergedEnv = createCleanMcpEnvironment(config.env)

  const transport = new StdioClientTransport({
    command,
    args,
    env: mergedEnv,
    stderr: "ignore",
    // ⚠️ cwd 从未被提取和传递！
  })

  await client.connect(transport)
}
```

只提取了 `command`、`args`、`env`，**`cwd` 被完全忽略**。

#### 5. `StdioClientTransport` 实际上支持 `cwd`

文件: `@modelcontextprotocol/sdk/client/stdio.ts`

```typescript
export type StdioServerParameters = {
  command: string
  args?: string[]
  env?: Record<string, string>
  stderr?: IOType | Stream | number
  cwd?: string     // <-- SDK 本身支持 cwd！
  maxBufferSize?: number
}

// 在 start() 中:
this._process = spawn(this._serverParams.command, this._serverParams.args ?? [], {
  env: { ... },
  cwd: this._serverParams.cwd,  // 如果传了就会用
  ...
})
```

MCP SDK 的 `StdioClientTransport` **确实接受 `cwd` 参数**，并在 `spawn` 中正确地传递给子进程。但 oh-my-openagent 调用时没有传。

### 结果

```
OpenCode 进程 CWD = D:\Unity Project\FrameworkTest\  (项目根目录)
  └─ spawn: uv run hn-unity-mcp  (cwd=undefined → 继承父进程 CWD)
       └─ uv 在当前目录找 pyproject.toml → ❌ 没找到
       └─ uv 尝试找系统命令 hn-unity-mcp → ❌ 不存在
       └─ 进程崩溃退出 → Connection closed
```

### 验证实验

| 实验 | 工作目录 | 命令 | 结果 |
|------|---------|------|------|
| 原始 (无 cwd) | 项目根目录 | `uv run hn-unity-mcp` | ❌ `error: program not found` |
| 有 cwd | Python 项目目录 | `uv run hn-unity-mcp` | ✅ MCP 握手成功 |
| `--directory` 修复 | 项目根目录 | `uv run --directory <abs> hn-unity-mcp` | ✅ MCP 握手成功 |
| venv python 直接启动 | 项目根目录 | `python -c "..."` + PYTHONPATH | ✅ MCP 握手成功 |

## 解决方案

有两种最小改动方案，均不需要修改 oh-my-openagent 源码：

### 方案 A（已采用）：`uv --directory` 参数

利用 `uv` 自身的 `--directory` 参数指定项目目录，绕过了对 `cwd` 的依赖。

```json
{
  "mcpServers": {
    "hn-unity-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "D:\\Unity Project\\FrameworkTest\\.opencode\\skills\\game-dev_unity_hn-unity-mcp\\HNUnityMCP\\python",
        "hn-unity-mcp"
      ],
      "timeout": 30000
    }
  }
}
```

`uv run --directory <path> <script>` 告诉 uv 将 `<path>` 视为项目根目录，在那里查找 `pyproject.toml`。无论进程的 CWD 是什么都能正确工作。

### 方案 B：直接使用 venv Python

绕过 `uv`，直接用 venv 中的 Python 解释器运行 server，通过 `PYTHONPATH` 指定源码路径。

```json
{
  "mcpServers": {
    "hn-unity-mcp": {
      "command": "D:\\...\\python\\.venv\\Scripts\\python.exe",
      "args": ["-c", "import asyncio; from hn_unity_mcp.server import main; main()"],
      "env": {
        "PYTHONPATH": "D:\\...\\python\\src",
        "UNITY_MCP_HOST": "localhost",
        "UNITY_MCP_PORT": "18080"
      },
      "timeout": 30000
    }
  }
}
```

### 备注

- mcp.json 修改后需要**重启 OpenCode 会话**才能生效（当前会话已缓存旧配置）
- 所有路径需使用**绝对路径**，因为 `cwd` 被忽略，相对路径无法保证正确解析

## oh-my-openagent 修复建议

如果需要从根本上修复，oh-my-openagent 需要修改两处源码：

1. **`src/features/claude-code-mcp-loader/types.ts`** — `ClaudeCodeMcpServer` 增加 `cwd` 字段
2. **`src/features/skill-mcp-manager/manager.ts`** — `createStdioClient()` 将 `cwd` 传给 `StdioClientTransport`

```typescript
// types.ts
export interface ClaudeCodeMcpServer {
  // ... 现有字段
  cwd?: string   // 新增
}

// manager.ts createStdioClient()
const transport = new StdioClientTransport({
  command,
  args,
  env: mergedEnv,
  stderr: "ignore",
  cwd: config.cwd,  // 新增
})
```

## 参考链接

- oh-my-openagent 仓库: https://github.com/code-yeongyu/oh-my-openagent
- skill_mcp 工具源码: `src/tools/skill-mcp/tools.ts`
- SkillMcpManager 源码: `src/features/skill-mcp-manager/manager.ts`
- MCP SDK StdioClientTransport: `@modelcontextprotocol/sdk/client/stdio.ts`
- Skill loader MCP 配置加载: `packages/skills-loader-core/src/features/opencode-skill-loader/skill-mcp-config.ts`
