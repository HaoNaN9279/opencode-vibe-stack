---
name: custom-tool
description: 当用户需要创建或管理 OpenCode 自定义工具（Custom Tool）时使用
license: MIT
compatibility: opencode
metadata:
  audience: contributors
  category: configuration
---

# Custom Tool — 自定义工具制作指南

指导在 **opencode-vibe-stack** 中创建和管理 OpenCode 自定义工具。自定义工具是 LLM 可在对话中调用的函数，使用 TypeScript/JavaScript 通过 `tool()` 辅助函数（来自 `@opencode-ai/plugin`）定义，可调用**任何语言**编写的脚本。

> **命名冲突**：自定义工具名称优先于同名内置工具。除非有意替换，否则使用独特名称。要禁用内置工具而不覆盖，用[权限](https://opencode.ai/docs/zh-cn/permissions/)控制。

---

## 部署位置

### 确定添加内容的位置

当用户描述添加内容时，按以下规则确定存放位置的层级：

- **"添加常驻内容"** 或类似描述 → `core/` 目录（全局常驻配置）
- **"为 xxx domain" / "xxx 领域" / "为 xxx 添加内容"** 或类似描述 → `domains/<category>/<domain>/` 目录（领域专属配置）
- **"为当前项目添加内容"** 或类似描述 → `.opencode/` 目录（项目专属配置）
- **"为本地用户配置" / "为本地用户"** 或类似描述 → `~/.config/opencode/` 目录（用户本地配置）
- **未明确指明位置** → **必须询问用户**具体的添加位置，绝对不允许擅自做决策

工具按作用域放在以下三个位置之一（结构一致，路径不同）：

| 作用域 | 路径 |
|--------|------|
| **全局**（所有项目可用） | `core/tools/<name>.ts` → `~/.config/opencode/tools/` |
| **领域**（领域激活时生效） | `domains/<category>/<domain>/tools/<name>.ts` |
| **项目**（仅当前项目） | `.opencode/tools/<name>.ts` |

多工具可用目录分组：`core/tools/<group>/<name>.ts`。

---

## 工具定义格式

### 单工具文件

文件名即为工具名。使用 `tool()` 默认导出：

```typescript
// .opencode/tools/query-database.ts
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Query the project database",
  args: {
    query: tool.schema.string().describe("SQL query to execute"),
  },
  async execute(args) {
    return `Executed query: ${args.query}`
  },
})
```

### 单文件多工具

命名导出，工具名为 **`<filename>_<exportname>`**：

```typescript
// .opencode/tools/math.ts
import { tool } from "@opencode-ai/plugin"

export const add = tool({ description: "Add two numbers", args: { a: tool.schema.number().describe("First number"), b: tool.schema.number().describe("Second number") }, async execute(args) { return args.a + args.b } })
export const multiply = tool({ description: "Multiply two numbers", args: { a: tool.schema.number().describe("First number"), b: tool.schema.number().describe("Second number") }, async execute(args) { return args.a * args.b } })
```

生成工具：`math_add`、`math_multiply`。

---

## 参数定义

使用 `tool.schema`（基于 [Zod](https://zod.dev)）定义类型：

```typescript
args: {
  query: tool.schema.string().describe("SQL query to execute"),
  limit: tool.schema.number().optional().describe("Max results"),
  format: tool.schema.enum(["json", "csv"]).describe("Output format"),
}
```

也可直接使用 Zod：

```typescript
import { z } from "zod"
export default { description: "...", args: { param: z.string().describe("...") }, async execute(args, context) { return "result" } }
```

### 支持的类型

| 方法 | TypeScript 类型 | 说明 |
|------|-----------------|------|
| `tool.schema.string()` | `string` | 字符串 |
| `tool.schema.number()` | `number` | 数字 |
| `tool.schema.boolean()` | `boolean` | 布尔值 |
| `tool.schema.enum([...])` | 枚举 | 固定可选值 |
| `.optional()` | `T \| undefined` | 可选参数 |
| `.default(val)` | 带默认值 | 默认值参数 |
| `.describe(str)` | — | 参数描述（LLM 理解用） |

---

## 上下文 API

`execute` 的第二个参数接收会话上下文：

```typescript
async execute(args, context) {
  const { agent, sessionID, messageID, directory, worktree } = context
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent` | `string` | 当前代理名称 |
| `sessionID` | `string` | 当前会话 ID |
| `messageID` | `string` | 当前消息 ID |
| `directory` | `string` | 会话工作目录 |
| `worktree` | `string` | Git worktree 根目录 |

---

## 调用外部脚本

工具定义可调用任意语言脚本。示例：Python 加法工具。

创建 `add.py`：

```python
import sys; print(int(sys.argv[1]) + int(sys.argv[2]))
```

工具定义通过 `Bun.$` 调用：

```typescript
// .opencode/tools/python-add.ts
import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Add two numbers using Python",
  args: { a: tool.schema.number().describe("First number"), b: tool.schema.number().describe("Second number") },
  async execute(args, context) {
    const script = path.join(context.worktree, ".opencode/tools/add.py")
    return (await Bun.$`python3 ${script} ${args.a} ${args.b}`.text()).trim()
  },
})
```

### 支持的脚本语言

| 语言 | 调用方式 |
|------|----------|
| Python | `Bun.$`python3 ${script} ${args}`.text()` |
| Node.js | `Bun.$`node ${script} ${args}`.text()` |
| Bash | `Bun.$`bash ${script} ${args}`.text()` |
| 任意二进制 | 直接调用 |

> 在 vibe-stack 领域中推荐使用**预构建二进制**（类似 MCP），避免运行时依赖。

---

## 在 vibe-stack 中管理

**核心工具**：放在 `core/tools/`，通过 `install.sh` / `install.ps1` 自动链接到 `~/.config/opencode/tools/`。

**领域工具**：放在 `domains/<cat>/<domain>/tools/`，通过 `vibe-stack activate <domain>` 扫描该目录下所有 `*.ts` 文件，符号链接到项目 `.opencode/tools/`，OpenCode 启动时自动注册。

---

## 最佳实践

| 维度 | 要点 |
|------|------|
| **命名** | 动词开头、职责单一：`query-database` ✓ / `database` ✗ |
| **参数** | 每个参数加 `.describe()`；可选用 `.optional()`；合理设 `.default()` |
| **返回值** | 返回含摘要的字符串，方便 LLM 理解执行结果 |
| **错误处理** | try/catch 捕获异常，返回友善的错误消息 |
| **幂等性** | 工具应可重复调用而不产生意外副作用 |
| **安全** | 验证输入防注入；不硬编码密钥，用环境变量；用 `path.join()` 构建路径 |
| **性能** | 耗时操作加超时机制，避免阻塞 LLM 会话 |
| **集成** | 领域工具不污染全局命名空间；多工具文件用 `<group>_<name>` 隔离 |

---

## 完整示例

`domains/ai/data_forge/tools/data-validate.ts`：

```typescript
import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Validate AI training data format and schema compliance",
  args: {
    filePath: tool.schema.string().describe("Path to the data file to validate"),
    schema: tool.schema.enum(["image-classification", "object-detection", "text"]).optional().default("image-classification").describe("Data schema type"),
  },
  async execute(args, context) {
    const fullPath = path.resolve(context.directory, args.filePath)
    try {
      const result = await Bun.$`python3 ${context.worktree}/tools/validate.py ${fullPath} --schema ${args.schema}`.text()
      return `Validation complete: ${result.trim()}`
    } catch (error) {
      return `Validation failed: ${error instanceof Error ? error.message : String(error)}`
    }
  },
})
```
