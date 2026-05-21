---
description: "扫描当前项目，自动识别所需的技术领域，并链接对应的 domain 模块到项目 opencode/ 目录"
agent: build
---

# workspace_init

## 概述

扫描当前项目目录，通过 explore agent 识别项目类型和技术栈，
从 `domain.config` 中匹配需要的 domain 模块，
以逐个文件/目录链接的方式安装到项目的 `opencode/` 目录下。

## 部署策略

OpenCode 只识别以下目录下的直接内容（不支持嵌套目录）：

```
~/.config/opencode/agents/      ← 逐个链接 core/agents/*.md
~/.config/opencode/rules/       ← 逐个链接 core/rules/*.md
~/.config/opencode/skills/      ← 逐个链接 core/skills/<name>/ 目录
~/.config/opencode/commands/    ← 逐个链接 core/commands/*.md

<project>/opencode/agents/      ← workspace_init 按领域链接
<project>/opencode/rules/       ← workspace_init 按领域链接
<project>/opencode/skills/      ← workspace_init 按领域链接
<project>/opencode/commands/    ← workspace_init 按领域链接
```

## 执行步骤

### 1. 探索项目

使用 explore agent 扫描当前目录：

- 检查配置文件（package.json、*.csproj、CMakeLists.txt、*.uproject 等）
- 检查源代码文件类型（*.ts、*.cs、*.py、*.cpp 等）
- 检查特定目录结构（Assets/、Editor/ 等）
- 收集项目使用的语言、框架、工具信息

### 2. 匹配 domain

- 读取 `~/.config/opencode/domain.config`（由 deploy.sh 生成）
- 将探索结果中的 indicators 与每个 domain 条目交叉匹配
- 匹配规则：
  - `file` 指标：检查是否存在匹配的 glob 模式文件，可选 `contains` 检查文件内容
  - `dir` 指标：检查是否存在指定目录
- 整理出匹配的 domain 列表

### 3. 链接 domain 到项目

对每个匹配的 domain，遍历其子目录并链接到项目 `opencode/`：

```
对每个匹配的 domain D:

  agents/
     遍历 domains/<D.path>/agents/*.md
    → 以 <D.name>.原文件名 链接到 opencode/agents/
    前缀避免不同 domain 的同名 agent 冲突

  rules/
     遍历 domains/<D.path>/rules/*.md
    → 保持原名链接到 opencode/rules/
    （规则文件名已具有唯一性）

  skills/
    遍历 domains/<D.path>/skills/*/（子目录）
    → 保持原名链接到 opencode/skills/
    （skill 目录名已具有唯一性）

  commands/
     遍历 domains/<D.path>/commands/*.md
    → 以 <D.name>.原文件名 链接到 opencode/commands/
```

### 4. 同步逻辑

每次执行 workspace_init 都使用同步策略：

1. **源→目标**：遍历每个 domain 的源目录，创建/修正/跳过链接
   - 链接不存在 → 创建
   - 链接存在且指向正确 → 跳过
   - 链接存在但指向错误 → 删除重建
2. **目标→源反向**：清理过期链接
   - 如果 `opencode/` 下存在本工具链的链接（指向 `${OPCODE_STACK_ROOT}/domains/`），
     但其源文件已不在当前匹配的 domain 中 → 移除

### 5. 生成 workspace 配置

- 在项目根目录创建/更新 `opencode/workspace.md`
- 记录匹配到的 domain 列表

```yaml
---
version: "2.1"
name: "<项目名称>"
domains:
  - "game-engine.unity.csharp-api"
  - "dcc.blender.python-api"
---
```

### 6. 输出摘要

向用户报告：
- 项目类型识别结果
- 匹配到的 domain 列表
- 每个 domain 链接的文件/目录统计
- 清理的过期链接数量

## 注意事项

- domain.config 路径优先使用 `${OPCODE_STACK_ROOT}/core/domain.config`
- 链接时自动创建 `opencode/` 下需要的子目录（agents/、rules/、skills/、commands/）
- 仅处理非空的 domain 模块（至少包含 agents/、commands/、rules/、skills/ 之一）
- 如果项目已有自定义的同名文件（非链接），备份为 `.bak` 后创建链接
---
