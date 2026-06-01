---
description: 自动查看 diff、生成 commit message 并提交（不 push）
model: opencode/deepseek-v4-flash-free
---

# `/auto-git-commit` — 自动 Git 提交

根据当前项目的 Git 变更，自动生成规范的 commit message 并提交，**不推送**到远程。

## 执行步骤

### Step 1: 检查 Git 状态

运行 `git status` 查看当前工作区状态，确认是否有已修改/已暂存的文件。

### Step 2: 获取详细 Diff

运行 `git diff --staged` 查看暂存区的变更。如果有未暂存的变更，也要运行 `git diff` 查看工作区变更。

如果存在未暂存的变更，同时也要检查是否有新增的未跟踪文件（`git status` 的输出中会有提示）。

### Step 3: 生成 Commit Message

根据 diff 内容，遵循 Conventional Commits 规范生成简洁但描述清晰的 commit message：

```
<type>(<scope>): <简短描述>

<详细说明（可选）>
```

- **type**: feat / fix / refactor / chore / docs / style / test / perf / ci / build / revert
- **scope**: 影响的主要模块/目录（可选）
- **描述**: 中文或英文，与项目现有风格保持一致

### Step 4: 提交

1. 如果有未暂存的变更（包括新文件），先执行 `git add -A` 暂存所有变更
2. 使用上一步生成的 commit message 执行 `git commit -m "<message>"`
3. **不要执行** `git push`

### Step 5: 报告结果

提交完成后，输出提交的 hash、message 摘要，以及当前分支状态。

## 注意事项

- 只提交，**绝不 push**
- 如果没有任何变更，告知用户并退出
- Commit message 应当清晰反映变更内容，避免无意义的 message（如 "fix"、"update"、"changes"）
- 如果 diff 很大，提取关键变更进行概括，不必逐行描述
