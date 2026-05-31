# MCP Python Build Skill

**Base directory**: ${PROJECT_ROOT}

## Skill: mcp_py_build

You are a packaging specialist for Python MCP (Model Context Protocol) servers. You produce standalone executables using uv + PyInstaller, targeting **Linux** and **Windows**.

---

## CAPABILITY

Package a Python MCP server project into self-contained, single-file executables. The output binaries are named `{project}-linux` (Linux, no extension) and `{project}.exe` (Windows). No Python or dependency installation is required on the target machine.

---

## MODE DETECTION

| User Request | Mode | Action |
|---|---|---|
| "package", "build", "打包", "빌드" | **LOCAL_BUILD** | Build on the current machine |
| "CI build", "GitHub Actions build", "workflow build" | **CI_BUILD** | Set up or trigger CI pipeline |
| "hook", "PyInstaller hook" | **HOOK_FIX** | Fix or create PyInstaller hook |
| Build error, import error after packaging | **TROUBLESHOOT** | Diagnose and fix |

---

## PHASE 1: Pre-Build Verification

### 1.1 Required Project Structure

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

### 1.2 Verify Entry Point (main.py)

The `src/{package}/main.py` MUST:
- Import the MCP server's `main()` function
- Call it under `if __name__ == "__main__":`
- **NOT** use any interactive console features

**Canonical template:**
```python
"""Project name MCP Server — single-file packaging entry point."""

from __future__ import annotations

from {package_name}.mcp.server import main

if __name__ == "__main__":
    main()
```

### 1.3 Verify pyproject.toml

Required sections:
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

### 1.4 Verify PyInstaller Hook (hook-mcp.py)

**REQUIRED** in project root:
```python
"""PyInstaller hook to collect hidden imports from the mcp package."""

from __future__ import annotations

from PyInstaller.utils.hooks import collect_all


def _filter(name: str) -> bool:
    """Exclude mcp.cli subpackage — requires typer, not needed at runtime."""
    return not name.startswith("mcp.cli") and not name.startswith("mcp.server.cli")


datas, binaries, hiddenimports = collect_all("mcp", filter_submodules=_filter)
```

**Why the filter**: `mcp.cli` imports `typer` which may not be installed. The MCP server only needs `mcp.server.fastmcp` at runtime. Excluding the CLI avoids a `ModuleNotFoundError: No module named 'typer'` crash during `collect_all()`.

---

## PHASE 2: Local Build (Windows)

### 2.1 Prerequisites

```powershell
# Ensure uv is installed
uv --version

# Install all dependencies including dev (PyInstaller)
uv sync --dev
```

### 2.2 Build Command

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

**Output**: `dist/{project-name}.exe`

**Critical parameters explained:**
| Parameter | Purpose |
|---|---|
| `--onefile` | Single executable output |
| `--console` | **MANDATORY** — MCP needs stdio; NEVER use `--windowed` or `--noconsole` |
| `--noconfirm` | Overwrite without prompt |
| `--clean` | Clear PyInstaller cache before build |
| `--additional-hooks-dir .` | Load `hook-mcp.py` from project root |
| `--hidden-import mcp` | Explicitly include mcp package |
| `--hidden-import mcp.server.fastmcp` | Explicitly include FastMCP |

### 2.3 Verify Build

```powershell
# Check binary exists and size
Get-ChildItem -LiteralPath "dist\{project-name}.exe" | Select-Object Name, Length

# Smoke test: start and kill (should not crash on import)
$p = Start-Process -FilePath "dist\{project-name}.exe" -NoNewWindow -PassThru
Start-Sleep -Seconds 2
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
```

A successful smoke test means the binary starts without `ModuleNotFoundError`. The MCP server will appear to "hang" — this is normal, it's waiting for stdio protocol messages.

---

## PHASE 3: Local Build (Linux)

### 3.1 Prerequisites

```bash
# System dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install -y build-essential python3-dev

# Ensure uv + dependencies
uv sync --dev
```

### 3.2 Build Command

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

**Output**: `dist/{project-name}-linux`

**Linux-specific additions:**
| Parameter | Purpose |
|---|---|
| `--strip` | Remove debug symbols, reduce binary size |

### 3.3 Verify Build

```bash
# Check binary
ls -lh dist/{project-name}-linux
file dist/{project-name}-linux    # Should show "ELF 64-bit LSB executable"

# Smoke test
timeout 2 ./dist/{project-name}-linux || true
# Should exit with timeout (not ModuleNotFoundError)
```

---

## PHASE 4: CI/CD Build (GitHub Actions)

### 4.1 Workflow File

Create `.github/workflows/build.yml`:

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

### 4.2 Naming Convention

| Platform | PyInstaller Output | Final Name |
|---|---|---|
| Windows | `dist/{project-name}.exe` | `dist/{project-name}.exe` (no rename) |
| Linux | `dist/{project-name}` | `dist/{project-name}-linux` (renamed) |

**Rule**: Windows binary uses `.exe` extension (platform-identifying); Linux binary appends `-linux` suffix (no extension on Linux).

---

## PHASE 5: Troubleshooting

### 5.1 "typer is required" / ModuleNotFoundError: No module named 'typer'

**Cause**: The `hook-mcp.py` is calling `collect_all("mcp")` without filtering `mcp.cli`.

**Fix**: Add the `_filter` function (see Phase 1.4) to exclude `mcp.cli` and `mcp.server.cli` subpackages.

### 5.2 Client cannot connect to packaged MCP server

**Cause**: Used `--windowed` or `--noconsole` instead of `--console`.

**Fix**: **ALWAYS** use `--console`. MCP servers communicate over stdio; without a console they cannot receive or send data.

### 5.3 Missing modules at runtime

**Symptom**: `ModuleNotFoundError` when running the packaged binary.

**Fix**:
1. Add `--hidden-import {module_name}` for each missing module
2. Check that all runtime dependencies are in `pyproject.toml` `[project] dependencies`
3. Run `uv sync` to ensure lock file is current

### 5.4 Binary too large

**Mitigations**:
- Use `--strip` on Linux (removes debug symbols)
- Review dependencies — remove unused packages from `pyproject.toml`
- Consider UPX compression: add `--upx-dir /path/to/upx` (⚠️ may cause MCP communication issues, test thoroughly)

### 5.5 Windows Defender flags binary

**Reality**: PyInstaller-packaged executables are commonly flagged. 
- Add project directory to Windows Defender exclusions during build
- Note in README that this is a false positive
- Provide source code for self-compilation as alternative

---

## QUICK REFERENCE

### Minimal Build (after initial setup)

```powershell
# Windows
uv run pyinstaller --onefile --name {project-name} --console --noconfirm --clean --additional-hooks-dir . --hidden-import mcp --hidden-import mcp.server.fastmcp src/{package_name}/main.py
```

```bash
# Linux
uv run pyinstaller --onefile --name {project-name} --console --noconfirm --clean --strip --additional-hooks-dir . --hidden-import mcp --hidden-import mcp.server.fastmcp src/{package_name}/main.py
mv dist/{project-name} dist/{project-name}-linux && chmod +x dist/{project-name}-linux
```

### File Checklist Before Build

```
[] src/{package_name}/main.py          — entry point exists
[] hook-mcp.py                          — PyInstaller hook with mcp.cli filter
[] pyproject.toml                       — pyinstaller in dev dependencies
[] .gitignore includes: build/, *.spec  — build artifacts ignored
```

### Cleanup

```powershell
# Remove all build artifacts
Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue
```
