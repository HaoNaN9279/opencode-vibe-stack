# MCP Python 发布技能

**基础目录**：${PROJECT_ROOT}

## 技能：mcp_py_release

你是 Python MCP (Model Context Protocol) 服务器项目的发布管理员。你处理版本升级、git 标签管理、推送和 GitHub Release 创建——这些操作通过 GitHub Actions 自动触发。

---

## 能力描述

管理已打包 MCP 服务器的完整发布生命周期：
1. 使用正确的原子提交提交所有更改
2. 在 `pyproject.toml` 中升级版本号
3. 创建并推送 `v*` 标签以触发 CI 构建
4. 验证 GitHub Actions 构建和 Release 创建

---

## 模式检测

| 用户请求 | 模式 | 操作 |
|---|---|---|
| "release", "publish", "发布", "릴리스" | **FULL_RELEASE** | 提交 → 升级 → 标签 → 推送 |
| "tag", "create tag", "打标签" | **TAG_ONLY** | 仅创建并推送标签 |
| "version bump", "bump version" | **VERSION_BUMP** | 更新 pyproject.toml 中的版本号 |
| 发布卡住，CI 失败 | **TROUBLESHOOT** | 诊断工作流失败原因 |

---

## 阶段 1：发布前验证

### 1.1 检查当前状态

并行执行所有命令：

```bash
# Project state
git status
git log --oneline -5

# Current version
grep 'version = ' pyproject.toml

# Check CI workflow exists
ls .github/workflows/build.yml

# Check remote
git remote -v
```

### 1.2 发布前检查清单

```
[] build.yml exists in .github/workflows/
[] All changes staged/committed (git status clean)
[] Local build tested: uv run pyinstaller ... succeeds
[] Version number decided (see Phase 2)
[] Working on correct branch (not detached HEAD)
```

**硬性停止**：如果缺少 `build.yml`，推送标签将**不会**触发构建。首先使用 `mcp_py_build` 技能的 CI 模板创建工作流文件。

---

## 阶段 2：版本升级

### 2.1 确定版本号

从 `pyproject.toml` 读取当前版本号：
```toml
[project]
name = "data-forge"
version = "0.2.0"
```

**版本升级规则：**
| 变更类型 | 升级方式 | 示例 |
|---|---|---|
| 仅修复 Bug | 补丁 (0.0.x) | 0.2.0 → 0.2.1 |
| 新增功能，向后兼容 | 次版本 (0.x.0) | 0.2.0 → 0.3.0 |
| 破坏性变更 | 主版本 (x.0.0) | 0.2.0 → 1.0.0 |
| 预发布 | 追加 -alpha.N、-beta.N、-rc.N | 0.3.0-alpha.1 |

**如果版本号不明确，请询问用户。** 不要猜测是否破坏性变更。

### 2.2 更新 pyproject.toml

```toml
# Before
version = "0.2.0"

# After (patch bump)
version = "0.2.1"
```

直接编辑文件——替换 `[project]` 配置段中的版本号字符串。

### 2.3 验证版本号一致性

```bash
# Confirm version updated correctly
grep 'version = ' pyproject.toml
```

---

## 阶段 3：提交策略

### 3.1 提交信息规范

所有与发布相关的提交使用**语义化**风格：

```
chore: bump version to 0.2.1
chore: add pyinstaller hook for mcp server packaging
feat: add single-file packaging support
ci: add github actions build workflow
```

### 3.2 原子提交

**按关注点拆分**——绝不要捆绑无关的更改：

```
WRONG: 1 commit with "Release v0.2.1"
  - version bump, build.yml, main.py, hook-mcp.py all in one commit

RIGHT: Multiple focused commits:
  1. "chore: add packaging entry point"     → src/{package}/main.py
  2. "chore: add pyinstaller hook"          → hook-mcp.py
  3. "ci: add automated build workflow"     → .github/workflows/build.yml
  4. "chore: update gitignore for pyinstaller" → .gitignore
  5. "chore: bump version to 0.2.1"         → pyproject.toml
```

### 3.3 执行提交

对每个逻辑分组：

```powershell
# Stage specific files
$env:GIT_MASTER='1'; git add path/to/file1 path/to/file2

# Commit with semantic style
$env:GIT_MASTER='1'; git commit -m "type: description"
```

---

## 阶段 4：标签创建与推送

### 4.1 创建附注标签

```powershell
# Create annotated tag (REQUIRED — lightweight tags may not trigger CI)
$env:GIT_MASTER='1'; git tag -a v{version} -m "Release v{version}"

# Example
$env:GIT_MASTER='1'; git tag -a v0.2.1 -m "Release v0.2.1"
```

**标签命名**：必须为 `v{version}`（例如 `v0.2.1`），以匹配 CI 触发模式 `'v*'`。

### 4.2 推送提交与标签

```powershell
# Push commits first
$env:GIT_MASTER='1'; git push origin {branch-name}

# Then push tag (triggers CI build)
$env:GIT_MASTER='1'; git push origin v{version}
```

**关键**：在提交**之后**再推送标签。CI 工作流在推送标签时触发，并检出该标签指向的提交——如果版本升级提交尚未推送，标签将指向旧提交。

### 4.3 验证推送

```powershell
# Confirm tag exists on remote
$env:GIT_MASTER='1'; git ls-remote --tags origin | Select-String "v{version}"
```

---

## 阶段 5：CI 与 Release 验证

### 5.1 监控 GitHub Actions

推送标签后：

1. 前往 `https://github.com/{owner}/{repo}/actions`
2. 找到由标签推送触发的工作流运行
3. 监控两个任务：**Build with PyInstaller (Windows)** 和 **Build with PyInstaller (Linux)**

### 5.2 预期工作流行为

```
1. Tag push triggers workflow (on: push: tags: ['v*'])
2. Matrix runs: windows-latest + ubuntu-latest in parallel
3. Each job:
   a. Checks out tagged commit
   b. Sets up Python 3.10
   c. Installs uv
   d. Runs uv sync --dev
   e. Builds with PyInstaller
   f. Uploads artifact (builds-windows-latest, builds-ubuntu-latest)
4. Release step (only on tag push):
   a. Creates GitHub Release from tag
   b. Attaches binaries: {project}.exe + {project}-linux
   c. Auto-generates release notes
```

### 5.3 验证 Release 产物

CI 完成后：
- 前往 `https://github.com/{owner}/{repo}/releases`
- 确认新 release 已存在
- 验证两个二进制文件均已附加：
  - `{project-name}.exe` (Windows)
  - `{project-name}-linux` (Linux)

### 5.4 验证二进制内容（可选）

```powershell
# Download and test Windows binary
# Run: .\{project-name}.exe
# Should start without ModuleNotFoundError
```

---

## 阶段 6：故障排除

### 6.1 推送标签后 CI 未触发

**检查**：
1. 标签名称是否匹配 `v*` 模式？（例如 `v0.2.1`，不是 `release-0.2.1`）
2. 标签是否已推送（`git push origin v0.2.1`，不仅仅是本地）
3. 工作流文件是否在 `.github/workflows/build.yml`，而不是 `.github/workflows/build.yaml` 或拼写错误
4. 工作流是否在 `on: push:` 部分包含 `tags: - 'v*'`

### 6.2 构建失败："hook-mcp.py" 错误

**常见原因**：
- `mcp.cli` 未过滤 → 向 hook 添加过滤函数
- 缺少 `typer` 依赖 → 从 hook 收集中过滤掉 `mcp.cli`
- 钩子路径错误 → 文件必须在项目根目录，通过 `--additional-hooks-dir .` 引用

### 6.3 已创建 Release 但未附加二进制文件

**检查**：
1. 构建任务是否成功（release 步骤需要产物存在）
2. `softprops/action-gh-release@v2` 是否有正确的 `files: dist/*` 模式
3. 两个矩阵任务是否在 release 步骤之前完成
4. 上传产物步骤是否使用了 `path: dist/*`（而不是 `path: dist`）

### 6.4 Release 中二进制文件命名错误

**预期**：`{project}.exe` + `{project}-linux`

**如果错误**：
- Windows：移除任何 `mv`/`rename` 步骤（PyInstaller 已输出正确名称）
- Linux：确保 `mv dist/{project} dist/{project}-linux` 在 PyInstaller 之后运行

### 6.5 Linux 二进制文件权限被拒绝

**修复**：在 Linux 构建步骤的 `mv` 命令之后添加 `chmod +x dist/{project}-linux`。

---

## 快速参考

### 完整发布流程（所有代码更改已提交后）

```powershell
# 1. Bump version
# Edit pyproject.toml: version = "X.Y.Z" → "X.Y.Z+1"

# 2. Commit version bump
$env:GIT_MASTER='1'; git add pyproject.toml
$env:GIT_MASTER='1'; git commit -m "chore: bump version to X.Y.Z+1"

# 3. Push commits
$env:GIT_MASTER='1'; git push origin main

# 4. Tag and push (triggers CI)
$env:GIT_MASTER='1'; git tag -a vX.Y.Z+1 -m "Release vX.Y.Z+1"
$env:GIT_MASTER='1'; git push origin vX.Y.Z+1

# 5. Monitor: https://github.com/{owner}/{repo}/actions
```

### 发布检查清单

```
[] All code changes committed (separate commits, NOT bundled with version bump)
[] Version bumped in pyproject.toml [project] version
[] Version bump committed as chore: bump version to X.Y.Z
[] Tag created: vX.Y.Z (matches version)
[] Commits pushed first, then tag
[] CI workflow triggered and running
[] Both platform builds succeeded
[] Release created with both binaries attached
```

### Git 命令快速参考

```powershell
# Check status
git status
git log --oneline -10

# Version management
# (manually edit pyproject.toml)

# Commit
$env:GIT_MASTER='1'; git add <files>
$env:GIT_MASTER='1'; git commit -m "type: message"

# Tag
$env:GIT_MASTER='1'; git tag -a vX.Y.Z -m "Release vX.Y.Z"

# Push (commits first, then tag)
$env:GIT_MASTER='1'; git push origin main
$env:GIT_MASTER='1'; git push origin vX.Y.Z

# Verify
$env:GIT_MASTER='1'; git ls-remote --tags origin
```
