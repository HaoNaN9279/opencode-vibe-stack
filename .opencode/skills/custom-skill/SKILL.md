---
name: custom-skill
description: 在 vibe-stack 项目中创建 OpenCode 技能（Skill）的制作规范和完整指南
license: MIT
compatibility: opencode
metadata:
  audience: contributors
  category: configuration
---

# Custom Skill — 技能制作指南

指导你在 **opencode-vibe-stack** 项目中创建和管理 OpenCode 技能（Skill）。技能通过 `SKILL.md` 定义可复用的行为指令，智能体可通过原生的 `skill` 工具按需加载。

---

## 1. 技能概述

技能是封装在 `SKILL.md` 中的可复用指令集。与规则（自动加载）不同，技能通过 `skill` 工具**按需加载**——智能体可以查看可用技能列表，识别匹配的技能，并在需要时加载完整内容。

### 技能 vs 规则

| 维度 | 规则 (Rule) | 技能 (Skill) |
|------|-------------|-------------|
| 加载方式 | 自动注入到上下文 | 按需通过 `skill` 工具加载 |
| 作用范围 | 全局/项目级 | 全局/项目级 |
| 内容特点 | 通用行为约束 | 特定领域的详细工作流 |
| 触发机制 | 始终存在 | 智能体识别到匹配时加载 |
| 上下文影响 | 始终占用 | 仅在需要时占用 |

---

## 2. 在 vibe-stack 中的部署位置

### 2.1 核心技能（全局可用）

放置在 `core/skills/` 目录下。安装时通过符号链接部署到 `~/.config/opencode/skills/`。

```
core/skills/
  └── <skill-name>/
      └── SKILL.md
```

### 2.2 领域技能（领域专属）

放置在 `domains/<category>/<domain>/skills/` 目录下。通过 `vibe-stack activate` 激活后部署。

```
domains/<category>/<domain>/
  skills/
    └── <skill-name>/
        └── SKILL.md
```

### 2.3 技能发现路径

OpenCode 按以下顺序搜索技能：

| 优先级 | 路径 | 说明 |
|--------|------|------|
| 1 | `.opencode/skills/<name>/SKILL.md` | 项目级技能 |
| 2 | `~/.config/opencode/skills/<name>/SKILL.md` | 全局技能 |
| 3 | `.claude/skills/<name>/SKILL.md` | Claude Code 兼容（项目） |
| 4 | `~/.claude/skills/<name>/SKILL.md` | Claude Code 兼容（全局） |
| 5 | `.agents/skills/<name>/SKILL.md` | 代理兼容（项目） |
| 6 | `~/.agents/skills/<name>/SKILL.md` | 代理兼容（全局） |

项目级路径会从当前工作目录向上遍历直到 git 工作树根目录。

---

## 3. SKILL.md 文件格式规范

### 3.1 目录结构

每个技能需要一个独立的目录，目录名即为技能名，目录内包含 `SKILL.md` 文件：

```
<skill-name>/
  └── SKILL.md
```

### 3.2 Frontmatter（必需）

每个 `SKILL.md` 必须以 YAML frontmatter 开头：

```yaml
---
name: skill-name           # 必填：技能名称，符合命名规范
description: 技能描述      # 必填：长度 1-1024 字符
license: MIT               # 可选
compatibility: opencode    # 可选
metadata:                  # 可选：字符串到字符串的映射
  audience: contributors
  category: domain-config
---
```

### 3.3 命名规范

`name` 必须满足以下条件：

- 长度为 1-64 个字符
- 仅包含小写字母和数字，可用单个连字符分隔
- 不以 `-` 开头或结尾
- 不包含连续的 `--`
- 与包含 `SKILL.md` 的目录名称一致

等效正则表达式：`^[a-z0-9]+(-[a-z0-9]+)*$`

### 3.4 描述规范

`description` 必须为 1-1024 个字符。描述应足够具体，以便智能体能够正确识别和选择该技能。

好的描述示例：
```
Create consistent releases and changelogs using conventional commits
```
```
Execute image processing pipelines with Data Forge MCP tools
```

差的描述示例：
```
A skill for releases
```
```
数据处理相关
```

---

## 4. 技能内容编写指南

### 4.1 内容结构模板

```markdown
# 技能标题 — 简短说明

技能的核心用途和适用场景的概述。

## 模板

（可选）角色扮演模板，定义 AI 在加载此技能后应扮演的角色。

## 核心工作流

列出加载此技能后应遵循的具体步骤和规则：

- 步骤 1：...
- 步骤 2：...
- 步骤 3：...

## 参数

（可选）定义此技能支持的用户参数：
- **param1**: 说明
- **param2**: 说明

## 使用时机

明确说明此技能应在何时加载使用。
```

### 4.2 写作原则

| 原则 | 说明 |
|------|------|
| **可操作性** | 每条指令必须是 AI 可执行的步骤 |
| **完整性** | 独立完整，不依赖其他技能或规则 |
| **前置条件** | 明确列出执行前需要满足的条件 |
| **边界清晰** | 明确说明技能做什么和不做什么 |
| **错误处理** | 包含常见错误场景的处理指引 |
| **示例驱动** | 使用具体示例说明预期行为 |

### 4.3 现有技能参考

**vibe-stack 技能**（`core/skills/vibe-stack/SKILL.md`）- 领域配置管理技能：

```markdown
# Vibe Stack - 领域配置管理器

管理 AI 智能体工具链的领域特定配置。

## 概述
Vibe Stack 为 OpenCode + OhMyOpenAgent (OMO) 提供分层配置系统。

## 关键位置
| 路径 | 用途 |
|------|---------|
| `~/.opencode-vibe-stack/core/` | 始终加载的常驻配置 |

## 使用命令
当你需要管理领域配置时，使用 `vibe-stack` CLI：

## 配置分层
## MCP 服务器管理
```

**data-forge 技能**（`domains/ai/data_forge/skills/data-forge/SKILL.md`）- 领域数据处理技能：

```markdown
# AI 训练数据流水线 (Data Forge)

使用 Data Forge MCP 工具包进行图像预处理、描述管理的专家级 AI 训练数据工程。

## 模板
你是一位专家级 AI 训练数据工程师...

在从事 AI 数据集项目时，你应：

- 使用 MCP 工具调用...
- 优先使用批量操作...
- ...

## 参数
- **topic**: 需要处理的特定数据集流水线任务
- **context**: 数据集大小、目标训练框架等
```

---

## 5. 技能的权限管理

### 5.1 全局权限

在 `opencode.json` 中控制技能访问权限：

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "pr-review": "allow",
      "internal-*": "deny",
      "experimental-*": "ask"
    }
  }
}
```

| 权限 | 行为 |
|------|------|
| `allow` | 技能立即加载 |
| `deny` | 对代理隐藏技能，拒绝访问 |
| `ask` | 加载前提示用户确认 |

### 5.2 按代理覆盖

**在自定义代理 frontmatter 中**：
```yaml
permission:
  skill:
    "documents-*": "allow"
```

**在内置代理配置中**：
```json
{
  "agent": {
    "plan": {
      "permission": {
        "skill": {
          "internal-*": "allow"
        }
      }
    }
  }
}
```

### 5.3 禁用技能工具

为不需要技能的代理完全禁用：

**自定义代理**：
```yaml
tools:
  skill: false
```

**内置代理**：
```json
{
  "agent": {
    "plan": {
      "tools": {
        "skill": false
      }
    }
  }
}
```

禁用后，`<available_skills>` 部分被完全省略。

---

## 6. 技能加载流程

### 6.1 发现阶段

OpenCode 启动时，扫描所有技能路径，在 `skill` 工具描述中列出可用技能：

```xml
<available_skills>
  <skill>
    <name>custom-rule</name>
    <description>在 vibe-stack 项目中创建 OpenCode 规则</description>
  </skill>
</available_skills>
```

### 6.2 加载阶段

AI 智能体通过调用 `skill` 工具加载技能：

```markdown
Invoke via: skill(name="skill-name")
```

### 6.3 排除加载问题

如果技能没有显示，检查：

1. 确认 `SKILL.md` 文件名全部为大写字母（S-K-I-L-L-.-m-d）
2. frontmatter 是否包含 `name` 和 `description`
3. 技能名称在所有位置中唯一
4. 权限设置是否正确（`deny` 的技能对代理隐藏）
5. 目录名与 `name` 字段一致

---

## 7. 创建技能的标准流程

```bash
# 1. 确定技能放置位置
# 全局技能 → core/skills/<skill-name>/SKILL.md
# 领域技能 → domains/<category>/<domain>/skills/<skill-name>/SKILL.md
# 项目技能 → .opencode/skills/<skill-name>/SKILL.md

# 2. 创建技能目录和文件
mkdir -p core/skills/my-skill
touch core/skills/my-skill/SKILL.md

# 3. 编写 frontmatter
# name: my-skill（目录名一致）
# description: 清晰具体的描述（1-1024 字符）

# 4. 编写技能内容
# - 角色定义
# - 核心工作流
# - 参数说明
# - 使用时机

# 5. 确保被技能路径发现
# 在 opencode.json 中配置 skills.paths
# 默认 core/skills/ 和 domains/*/*/skills/ 会被 OMO 自动发现

# 6. 测试技能加载
# 在会话中观察 AI 是否识别并加载该技能

# 7. 提交
git add core/skills/my-skill/
git commit -m "feat: add my-skill skill"
```

---

## 8. 设计原则与最佳实践

- **命名即标识**：技能名称是唯一标识，一旦确定不宜更改
- **描述即广告**：`description` 是智能体判断是否加载的依据，必须精准
- **自包含**：一个技能应独立完整，不依赖其他技能
- **按需加载**：不要用技能替代规则——规则是自动注入的，技能是按需加载的
- **参数化设计**：支持通过 `name()` 的参数传递上下文信息
- **适度粒度**：太粗（覆盖多个领域）或太细（每个函数一个技能）都不好
- **版本兼容**：在 `compatibility` 中标注兼容的 OpenCode 版本
- **用规则约束行为，用技能传授知识**：规则告诉 AI 不该做什么，技能告诉 AI 该怎么做
