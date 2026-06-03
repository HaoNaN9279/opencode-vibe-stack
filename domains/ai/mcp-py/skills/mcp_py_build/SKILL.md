---
name: mcp-py-build
description: 使用 uv + PyInstaller 将 Python MCP 服务器项目打包成独立可执行文件，支持 Linux 和 Windows 平台
---
# MCP Python 构建技能

**基础目录**：${PROJECT_ROOT}

## 技能：mcp_py_build

你是一名 Python MCP (Model Context Protocol) 服务器的打包专家。你使用 uv + PyInstaller 生成独立的可执行文件，目标平台为 **Linux** 和 **Windows**。

---

## 能力描述

将 Python MCP 服务器项目打包成自包含的单个文件可执行文件。输出二进制文件命名为 `{project}-linux`（Linux，无扩展名）和 `{project}.exe`（Windows）。目标机器上无需安装 Python 或依赖。

---

## 模式检测

| 用户请求 | 模式 | 操作 |
|---|---|---|
| "package", "build", "打包", "빌드" | **LOCAL_BUILD** | 在当前机器上构建 |
| "CI build", "GitHub Actions build", "workflow build" | **CI_BUILD** | 设置或触发 CI 流水线 |
| "hook", "PyInstaller hook" | **HOOK_FIX** | 修复或创建 PyInstaller hook |
| 构建错误，打包后导入错误 | **TROUBLESHOOT** | 诊断并修复 |

---

## 阶段 1：构建前验证

### 1.1 必需的项目结构

```
project-root/
├── src/
│   └── {package_name}/
│       ├── __init__.py
│       ├── main.py              # PyInstaller entry point (REQUIRED)
│       └── mcp/
│           └── server.py        # MCP server with main() calling mcp.run()
├── pyproject.toml
├── hook-mcp.py                  # PyInstaller hook (REQUIRED)
└── uv.lock
```

### 1.2 验证入口点 (main.py)

`src/{package}/main.py` **必须**：
- 导入 MCP 服务器的 `main()` 函数
- 在 `if __name__ == "__main__":` 下调用它
- **不能**使用任何交互式控制台功能

**标准模板：**
```python
"""Project name MCP Server — single-file packaging entry point."""

from __future__ import annotations

from {package_name}.mcp.server import main

if __name__ == "__main__":
    main()
```

### 1.3 验证 pyproject.toml

必需的配置段：
```toml
[project]
name = "{project-name}"
requires-python = ">=3.10"

dependencies = [
    "mcp>=1.0.0",
    # ... other runtime deps
]

[dependency-groups]
dev = [
    "pyinstaller>=6.0",
]

[project.scripts]
{project-name}-mcp = "{package_name}.mcp.server:main"
```

### 1.4 验证 PyInstaller 钩子 (hook-mcp.py)

**必需**在项目根目录：
```python
"""PyInstaller hook to collect hidden imports from the mcp package."""

from __future__ import annotations

from PyInstaller.utils.hooks import collect_all


def _filter(name: str) -> bool:
    """Exclude mcp.cli subpackage — requires typer, not needed at runtime."""
    return not name.startswith("mcp.cli") and not name.startswith("mcp.server.cli")


datas, binaries, hiddenimports = collect_all("mcp", filter_submodules=_filter)
```

**为什么需要过滤**：`mcp.cli` 导入了 `typer`，而 `typer` 可能未安装。MCP 服务器在运行时只需要 `mcp.server.fastmcp`。排除 CLI 可以避免 `collect_all()` 过程中因 `ModuleNotFoundError: No module named 'typer'` 导致的崩溃。

---

## 阶段 2：本地构建（Windows）

### 2.1 前置条件

```powershell
# Ensure uv is installed
uv --version

# Install all dependencies including dev (PyInstaller)
uv sync --dev
```

### 2.2 构建命令

```powershell
uv run pyinstaller `
  --onefile `
  --name {project-name} `
  --console `
  --noconfirm `
  --clean `
  --additional-hooks-dir . `
  --hidden-import mcp `
  --hidden-import mcp.server.fastmcp `
  src/{package_name}/main.py
```

**输出**：`dist/{project-name}.exe`

**关键参数说明：**
| 参数 | 目的 |
|---|---|
| `--onefile` | 单个可执行文件输出 |
| `--console` | **必须** — MCP 需要 stdio；绝不要使用 `--windowed` 或 `--noconsole` |
| `--noconfirm` | 覆盖时不提示 |
| `--clean` | 构建前清除 PyInstaller 缓存 |
| `--additional-hooks-dir .` | 从项目根目录加载 `hook-mcp.py` |
| `--hidden-import mcp` | 显式包含 mcp 包 |
| `--hidden-import mcp.server.fastmcp` | 显式包含 FastMCP |

### 2.3 验证构建

```powershell
# Check binary exists and size
Get-ChildItem -LiteralPath "dist\{project-name}.exe" | Select-Object Name, Length

# Smoke test: start and kill (should not crash on import)
$p = Start-Process -FilePath "dist\{project-name}.exe" -NoNewWindow -PassThru
Start-Sleep -Seconds 2
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
```

成功的冒烟测试意味着二进制文件启动时没有 `ModuleNotFoundError`。MCP 服务器看起来会"挂起"——这是正常的，它正在等待 stdio 协议消息。

---

## 阶段 3：本地构建（Linux）

### 3.1 前置条件

```bash
# System dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install -y build-essential python3-dev

# Ensure uv + dependencies
uv sync --dev
```

### 3.2 构建命令

```bash
uv run pyinstaller \
  --onefile \
  --name {project-name} \
  --console \
  --noconfirm \
  --clean \
  --strip \
  --additional-hooks-dir . \
  --hidden-import mcp \
  --hidden-import mcp.server.fastmcp \
  src/{package_name}/main.py

# Rename to include platform suffix
mv dist/{project-name} dist/{project-name}-linux
chmod +x dist/{project-name}-linux
```

**输出**：`dist/{project-name}-linux`

**Linux 特有参数：**
| 参数 | 目的 |
|---|---|
| `--strip` | 移除调试符号，减小二进制体积 |

### 3.3 验证构建

```bash
# Check binary
ls -lh dist/{project-name}-linux
file dist/{project-name}-linux    # Should show "ELF 64-bit LSB executable"

# Smoke test
timeout 2 ./dist/{project-name}-linux || true
# Should exit with timeout (not ModuleNotFoundError)
```

---

## 阶段 4：CI/CD 构建（GitHub Actions）

### 4.1 工作流文件

创建 `.github/workflows/build.yml`：

```yaml
name: Build {Project Name} MCP Server

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [windows-latest, ubuntu-latest]
        python-version: ["3.10"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Install dependencies
        run: uv sync --dev

      - name: Build with PyInstaller (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          uv run pyinstaller `
            --onefile `
            --name {project-name} `
            --console `
            --noconfirm `
            --clean `
            --additional-hooks-dir . `
            --hidden-import mcp `
            --hidden-import mcp.server.fastmcp `
            src/{package_name}/main.py

      - name: Build with PyInstaller (Linux)
        if: matrix.os == 'ubuntu-latest'
        run: |
          uv run pyinstaller \
            --onefile \
            --name {project-name} \
            --console \
            --noconfirm \
            --clean \
            --strip \
            --additional-hooks-dir . \
            --hidden-import mcp \
            --hidden-import mcp.server.fastmcp \
            src/{package_name}/main.py
          mv dist/{project-name} dist/{project-name}-linux
          chmod +x dist/{project-name}-linux

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: builds-${{ matrix.os }}
          path: dist/*

      - name: Create Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 4.2 命名规范

| 平台 | PyInstaller 输出 | 最终名称 |
|---|---|---|
| Windows | `dist/{project-name}.exe` | `dist/{project-name}.exe`（不重命名） |
| Linux | `dist/{project-name}` | `dist/{project-name}-linux`（已重命名） |

**规则**：Windows 二进制文件使用 `.exe` 扩展名（平台标识）；Linux 二进制文件添加 `-linux` 后缀（Linux 上无扩展名）。

---

## 阶段 5：故障排除

### 5.1 "typer is required" / ModuleNotFoundError: No module named 'typer'

**原因**：`hook-mcp.py` 在调用 `collect_all("mcp")` 时没有过滤 `mcp.cli`。

**修复**：添加 `_filter` 函数（见阶段 1.4）以排除 `mcp.cli` 和 `mcp.server.cli` 子包。

### 5.2 客户端无法连接到打包后的 MCP 服务器

**原因**：使用了 `--windowed` 或 `--noconsole` 而非 `--console`。

**修复**：**始终**使用 `--console`。MCP 服务器通过 stdio 通信；没有控制台就无法接收或发送数据。

### 5.3 运行时缺少模块

**症状**：运行打包后的二进制文件时出现 `ModuleNotFoundError`。

**修复**：
1. 为每个缺失的模块添加 `--hidden-import {module_name}`
2. 检查所有运行时依赖是否在 `pyproject.toml` 的 `[project] dependencies` 中
3. 运行 `uv sync` 确保 lock 文件是最新的

### 5.4 二进制文件过大

**缓解措施**：
- 在 Linux 上使用 `--strip`（移除调试符号）
- 审查依赖项——从 `pyproject.toml` 中移除未使用的包
- 考虑 UPX 压缩：添加 `--upx-dir /path/to/upx`（⚠️ 可能导致 MCP 通信问题，请彻底测试）

### 5.5 Windows Defender 标记二进制文件

**实际情况**：PyInstaller 打包的可执行文件经常被标记。
- 构建时将项目目录添加到 Windows Defender 排除列表
- 在 README 中说明这是误报
- 提供源码供自行编译作为替代方案

---

## 快速参考

### 最小化构建（初始设置完成后）

```powershell
# Windows
uv run pyinstaller --onefile --name {project-name} --console --noconfirm --clean --additional-hooks-dir . --hidden-import mcp --hidden-import mcp.server.fastmcp src/{package_name}/main.py
```

```bash
# Linux
uv run pyinstaller --onefile --name {project-name} --console --noconfirm --clean --strip --additional-hooks-dir . --hidden-import mcp --hidden-import mcp.server.fastmcp src/{package_name}/main.py
mv dist/{project-name} dist/{project-name}-linux && chmod +x dist/{project-name}-linux
```

### 构建前的文件检查清单

```
[] src/{package_name}/main.py          — entry point exists
[] hook-mcp.py                          — PyInstaller hook with mcp.cli filter
[] pyproject.toml                       — pyinstaller in dev dependencies
[] .gitignore includes: build/, *.spec  — build artifacts ignored
```

### 清理

```powershell
# Remove all build artifacts
Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue
```
