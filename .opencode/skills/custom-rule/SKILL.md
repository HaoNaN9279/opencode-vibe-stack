---
name: custom-rule
description: 在 vibe-stack 项目中创建 OpenCode 规则（AGENTS.md / rule 文件）的制作规范和完整指南
license: MIT
compatibility: opencode
metadata:
  audience: contributors
  category: configuration
---

# Custom Rule — 规则制作指南

指导你在 **opencode-vibe-stack** 项目中创建和管理 OpenCode 规则文件。规则为 AI 智能体提供自定义指令，所有规则通过 `AGENTS.md` 或单独的 `.md` 文件定义。

---

## 1. 规则体系概述

OpenCode 按以下优先级加载规则：

| 优先级 | 位置 | 文件 | 用途 |
|--------|------|------|------|
| 1（最高） | 项目目录（向上遍历） | `AGENTS.md` / `CLAUDE.md` | 项目级规则 |
| 2 | `~/.config/opencode/` | `AGENTS.md` | 全局规则 |
| 3 | `~/.claude/` | `CLAUDE.md` | Claude Code 兼容回退 |

**在同一类别中，先匹配到的文件优先。** 同时存在 `AGENTS.md` 和 `CLAUDE.md` 时，`AGENTS.md` 生效。

---

## 2. 在 vibe-stack 中的部署位置

规则文件依其作用范围放置在以下位置：

### 2.1 核心规则（全局生效）

放置在 `core/rules/` 目录下。安装时通过符号链接部署到 `~/.config/opencode/rules/`。

```
core/rules/
  ├── 00-global.md          # 适用于所有会话的全局规则
  └── <category>-<name>.md  # 其他全局规则
```

在 `opencode.json` 或 `oh-my-openagent.config.jsonc` 中通过 `instructions` 字段引用：

```json
{
  "instructions": [
    "~/.config/opencode/rules/*.md"
  ]
}
```

### 2.2 领域规则（领域专属）

放置在 `domains/<category>/<domain>/rules/` 目录下。通过 `vibe-stack activate` 激活后，通过符号链接部署到项目 `.opencode/` 目录。

```
domains/<category>/<domain>/
  rules/
    <domain>.md
```

### 2.3 项目级规则（项目根目录）

直接放置在项目根目录的 `AGENTS.md` 中，或通过 `opencode.json` 的 `instructions` 字段引用：

```json
{
  "instructions": [
    "CONTRIBUTING.md",
    "docs/guidelines.md",
    ".cursor/rules/*.md"
  ]
}
```

也支持远程 URL：

```json
{
  "instructions": [
    "https://raw.githubusercontent.com/my-org/shared-rules/main/style.md"
  ]
}
```

---

## 3. 规则文件格式规范

### 3.1 AGENTS.md 格式

`AGENTS.md` 使用 Markdown 格式，以 `#` 标题开头：

```markdown
# 项目名称

项目描述和背景信息。

## 项目结构
- `src/` — 源代码
- `tests/` — 测试文件

## 编码规范
- 使用 TypeScript strict 模式
- 遵循现有代码风格
```

### 3.2 独立规则文件格式（推荐用于 vibe-stack）

推荐使用独立 `.md` 文件，通过 `instructions` 字段引用。格式要求：

- **文件名**：使用 `NN-<name>.md` 前缀编号来控制加载顺序（如 `00-global.md`）
- **内容**：第一行为 `# 规则标题`，后续为具体规则内容
- **语言**：使用简体中文，专有名词保留原文
- **结构建议**：按主题分节，使用 `##` 二级标题

```markdown
# 全局规则

这些规则适用于所有 AI 智能体会话，无论项目或领域如何。

## 用户偏好
- 使用简体中文回答问题
- 专有名词和关键术语可以使用通用英文

## 一般行为规范
- 开始工作前，务必阅读项目中的 AGENTS.md 文件
- 遵循项目现有的代码风格和约定
```

### 3.3 引用外部文件

有两种方式引用外部文件：

**方式一：通过 `opencode.json` 的 `instructions` 字段（推荐）**

```json
{
  "instructions": [
    "docs/development-standards.md",
    "packages/*/AGENTS.md"
  ]
}
```

支持 glob 模式匹配多个文件。

**方式二：在 AGENTS.md 中通过 `@` 引用**

```markdown
对于 TypeScript 代码风格和最佳实践：@docs/typescript-guidelines.md
对于 React 组件架构：@docs/react-patterns.md
```

AI 智能体会在需要时按需读取这些文件。

---

## 4. 规则内容写作指南

### 4.1 规则结构模板

```markdown
# [规则类别]

简明描述这些规则的适用范围和目的。

## [具体主题 1]
- 规则点 1
- 规则点 2
- 规则点 3

## [具体主题 2]
- 规则点 1
- 规则点 2
```

### 4.2 写作原则

- **指令明确**：每条规则必须是可执行的指令，而非泛泛而谈
- **示例驱动**：复杂规则附带代码示例
- **负面清单**：明确禁止的行为用 "绝不" 强调
- **避免冗余**：不在多个规则文件中重复相同内容
- **版本相关**：涉及版本限制时标注版本号

### 4.3 规则类型建议

| 规则类型 | 放置位置 | 示例 |
|----------|----------|------|
| 全局行为规范 | `core/rules/00-global.md` | 沟通风格、安全策略 |
| 编码规范 | `core/rules/01-coding.md` | TypeScript 规范、命名约定 |
| 领域特定规则 | `domains/.../rules/<domain>.md` | Unity API 使用规范 |
| 工作流规则 | `core/rules/02-workflow.md` | Git 流程、PR 规范 |

---

## 5. 规则加载机制

OpenCode 通过以下方式发现规则：

1. **自动遍历**：从当前目录向上查找 `AGENTS.md` / `CLAUDE.md`
2. **指令引用**：读取 `opencode.json` 中 `instructions` 字段指定的文件
3. **全局位置**：检查 `~/.config/opencode/AGENTS.md`
4. **Claude 兼容**：检查 `~/.claude/CLAUDE.md`

### OMO 扩展加载

OhMyOpenAgent (OMO) 插件会从 `.opencode/` 和 `~/.config/opencode/` 目录下递归读取所有 `rules/` 目录中的 `.md` 文件，并通过内置的 `instructions` 机制注入到智能体上下文中。

---

## 6. 在 vibe-stack 中添加新规则的完整流程

```bash
# 1. 确定规则作用范围
# 全局规则 → core/rules/
# 领域规则 → domains/<category>/<domain>/rules/

# 2. 创建规则文件
echo "## My New Rule" > core/rules/03-my-rule.md

# 3. 如果使用独立规则文件模式，确保 opencode.json 或
#    oh-my-openagent.config.jsonc 的 instructions 中包含对应路径

# 4. 通过 vibe-stack 测试
vibe-stack status        # 确认激活状态
vibe-stack list          # 查看可用领域

# 5. 提交到版本控制
git add core/rules/03-my-rule.md
git commit -m "feat: add my-rule"
```

---

## 7. 最佳实践

- **使用编号前缀控制加载顺序**：`00-` 最先加载，`99-` 最后加载
- **规则文件保持专注**：每个文件只关注一个主题领域
- **定期审查**：移除过时规则，更新版本依赖
- **配合 skill 使用**：复杂的行为指南建议封装为 skill，规则只做通用约束
- **利用 Claude 兼容性**：可从 Claude Code 的 `CLAUDE.md` / `.claude/skills/` 迁移现有配置
