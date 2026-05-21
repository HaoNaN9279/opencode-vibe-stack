<#
.SYNOPSIS
OpenCode Vibe Coding 工具链部署脚本 - Windows
逐个链接 core 下的 agents/rules/skills/commands 到 %APPDATA%\OpenCode
支持重复执行：自动同步新增、修改和删除的文件
#>

param(
    [string]$StackRoot = $PWD.Path
)

$ErrorActionPreference = "Stop"
$StackRoot = (Resolve-Path $StackRoot).Path
$CoreSrc = Join-Path $StackRoot "core"
$OpenCodeDir = Join-Path ([Environment]::GetFolderPath("ApplicationData")) "OpenCode"

# ============================================================
# 工具函数
# ============================================================

function Sync-Files([string]$Type) {
    $srcDir = Join-Path $CoreSrc $Type
    $dstDir = Join-Path $OpenCodeDir $Type

    if (-not (Test-Path $srcDir)) { return }

    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    $seen = @()

    foreach ($srcFile in Get-ChildItem $srcDir -File) {
        $name = $srcFile.Name
        $dstFile = Join-Path $dstDir $name

        $seen += $name

        if (Test-Path $dstFile) {
            $item = Get-Item $dstFile -ErrorAction SilentlyContinue
            if ($item.LinkType -eq "SymbolicLink" -and $item.Target -eq $srcFile.FullName) {
                continue
            }
            if ($item.LinkType -eq "SymbolicLink") {
                Remove-Item $dstFile -Force
            } else {
                Move-Item $dstFile "$dstFile.bak.$(Get-Date -Format 'yyyyMMddHHmmss')" -Force
            }
        }

        New-Item -ItemType SymbolicLink -Path $dstFile -Target $srcFile.FullName -Force | Out-Null
        Write-Host "  + $Type/$name"
    }

    # 反向清理
    foreach ($dstFile in Get-ChildItem $dstDir -File) {
        $name = $dstFile.Name
        if ($dstFile.LinkType -eq "SymbolicLink") {
            $target = $dstFile.Target
            if ($target.StartsWith($CoreSrc)) {
                if ($name -notin $seen) {
                    Remove-Item $dstFile -Force
                    Write-Host "  - $Type/$name (已移除)"
                }
            }
        }
    }
}

function Sync-SkillDirs {
    $srcDir = Join-Path $CoreSrc "skills"
    $dstDir = Join-Path $OpenCodeDir "skills"

    if (-not (Test-Path $srcDir)) { return }

    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    $seen = @()

    foreach ($src in Get-ChildItem $srcDir -Directory) {
        $name = $src.Name
        $dst = Join-Path $dstDir $name

        $seen += $name

        if (Test-Path $dst) {
            $item = Get-Item $dst -ErrorAction SilentlyContinue
            if ($item.LinkType -eq "SymbolicLink" -and $item.Target -eq $src.FullName) {
                continue
            }
            if ($item.LinkType -eq "SymbolicLink") {
                Remove-Item $dst -Force -Recurse
            } else {
                Move-Item $dst "$dst.bak.$(Get-Date -Format 'yyyyMMddHHmmss')" -Force
            }
        }

        New-Item -ItemType SymbolicLink -Path $dst -Target $src.FullName -Force | Out-Null
        Write-Host "  + skills/$name/"
    }

    foreach ($dst in Get-ChildItem $dstDir -Directory) {
        $name = $dst.Name
        if ($dst.LinkType -eq "SymbolicLink") {
            $target = $dst.Target
            if ($target.StartsWith(Join-Path $CoreSrc "skills")) {
                if ($name -notin $seen) {
                    Remove-Item $dst -Force -Recurse
                    Write-Host "  - skills/$name/ (已移除)"
                }
            }
        }
    }
}

function Sync-Single([string]$SrcPath, [string]$DstPath, [string]$Label) {
    if (-not (Test-Path $SrcPath)) { return }

    $dstDir = Split-Path $DstPath -Parent
    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    if (Test-Path $DstPath) {
        $item = Get-Item $DstPath -ErrorAction SilentlyContinue
        if ($item.LinkType -eq "SymbolicLink" -and $item.Target -eq $SrcPath) {
            return
        }
        if ($item.LinkType -eq "SymbolicLink") {
            Remove-Item $DstPath -Force
        } else {
            Move-Item $DstPath "$DstPath.bak.$(Get-Date -Format 'yyyyMMddHHmmss')" -Force
        }
    }

    New-Item -ItemType SymbolicLink -Path $DstPath -Target $SrcPath -Force | Out-Null
    Write-Host "  + $Label"
}

# ============================================================
# 1. 环境变量
# ============================================================
Write-Host "============================================"
Write-Host "OpenCode Vibe Stack 部署 (Windows)"
Write-Host "============================================"
Write-Host ""

$currentRoot = [Environment]::GetEnvironmentVariable("OPCODE_STACK_ROOT", "User")
if ($currentRoot -ne $StackRoot) {
    [Environment]::SetEnvironmentVariable("OPCODE_STACK_ROOT", $StackRoot, "User")
    $env:OPCODE_STACK_ROOT = $StackRoot
    Write-Host ">> OPCODE_STACK_ROOT=$StackRoot"
} else {
    Write-Host ">> OPCODE_STACK_ROOT 已设置: $currentRoot"
}

# ============================================================
# 2. 清理旧版 core/ 整体链接
# ============================================================
$oldCoreLink = Join-Path $OpenCodeDir "User\core"
if (Test-Path $oldCoreLink) {
    $item = Get-Item $oldCoreLink -ErrorAction SilentlyContinue
    if ($item.LinkType -eq "SymbolicLink") {
        Write-Host ">> 清理旧版 core/ 整体链接..."
        Remove-Item $oldCoreLink -Force
    }
}

# ============================================================
# 3. 同步链接
# ============================================================
Write-Host ""
Write-Host ">> 同步链接 (core -> %APPDATA%\OpenCode)"

Write-Host "  agents/"
Sync-Files "agents"

Write-Host "  rules/"
Sync-Files "rules"

Write-Host "  skills/"
Sync-SkillDirs

Write-Host "  commands/"
Sync-Files "commands"

Sync-Single `
    (Join-Path $CoreSrc "mcp\mcp-config.json") `
    (Join-Path $OpenCodeDir "mcp-config.json") `
    "mcp-config.json"

Sync-Single `
    (Join-Path $CoreSrc "domain.config") `
    (Join-Path $OpenCodeDir "domain.config") `
    "domain.config"

# ============================================================
# 4. 扫描 domains/ 生成 domain.config
# ============================================================
Write-Host ""
Write-Host ">> 扫描 domains/ 目录..."

$domainsDir = Join-Path $StackRoot "domains"

$defaultIndicators = @{
    "web.nodejs.express"           = @(@{file="package.json"; contains="express"}, @{file="server.js"}, @{file="app.js"})
    "game-engine.unity.csharp-api" = @(@{file="*.cs"; contains="UnityEngine"}, @{file="*.unity"}, @{dir="Assets"}, @{dir="ProjectSettings"})
    "desktop.csharp.wpf"           = @(@{file="*.xaml"}, @{file="*.csproj"; contains="WinExe"}, @{file="App.xaml"}, @{file="*.cs"; contains="System.Windows"})
    "dcc.blender.python-api"       = @(@{file="*.py"; contains="bpy"}, @{file="__init__.py"; contains="bl_info"}, @{file="*.py"; contains="blender"})
    "dcc.houdini.vex"              = @(@{file="*.vfl"}, @{file="*.h"; contains="vop"}, @{file="*.hip"})
    "dcc.houdini.hdk"              = @(@{file="*.cpp"; contains="houdini"}, @{file="*.h"; contains="HAPI"}, @{file="CMakeLists.txt"; contains="houdini"})
}

$typeMap = @{
    express = "framework"; wpf = "framework"; hdk = "framework"
    unity = "game-engine"; blender = "dcc-tool"; houdini = "dcc-tool"
    vex = "language"
}

function Get-Type([string]$name) {
    foreach ($key in $typeMap.Keys) { if ($name -match $key) { return $typeMap[$key] } }
    return "unknown"
}
function Get-Category([string]$name) {
    return ($name -split "\.")[1]
}
function Has-Content([string]$p) {
    foreach ($sub in @("agents","commands","rules","skills")) {
        $sp = Join-Path $p $sub
        if ((Test-Path $sp) -and (Get-ChildItem $sp -ErrorAction SilentlyContinue).Count -gt 0) { return $true }
    }
    return $false
}

$entries = @()
if (Test-Path $domainsDir) {
    $leafDirs = Get-ChildItem $domainsDir -Recurse -Directory | Where-Object {
        ($_.FullName.Substring($domainsDir.Length).TrimEnd('\') -split [regex]::Escape([IO.Path]::DirectorySeparatorChar)).Count -eq 3
    }
    foreach ($dir in $leafDirs) {
        $relPath = $dir.FullName.Substring($domainsDir.Length + 1) -replace '\\', '/'
        $name = $relPath -replace '/', '.'
        $indicators = if ($defaultIndicators.ContainsKey($name)) { $defaultIndicators[$name] } else { @() }
        $entries += @{
            name = $name
            path = $relPath
            type = Get-Type $name
            category = Get-Category $name
            has_content = Has-Content $dir.FullName
            indicators = $indicators
        }
    }
}

$config = @{ version = "1.0"; entries = $entries }
$configPath = Join-Path $CoreSrc "domain.config"
$config | ConvertTo-Json -Depth 4 | Set-Content -Path $configPath -Encoding UTF8

$contentCount = ($entries | Where-Object { $_.has_content }).Count
Write-Host "  domain.config 已生成: $($entries.Count) 个模块, $contentCount 个包含内容"

# ============================================================
# 5. 完成
# ============================================================
Write-Host ""
Write-Host ">> 部署验证:"
Write-Host "  agents/ : $(Get-ChildItem (Join-Path $OpenCodeDir agents) -File -ErrorAction SilentlyContinue | Measure-Object | Select -ExpandProperty Count) 个文件"
Write-Host "  rules/  : $(Get-ChildItem (Join-Path $OpenCodeDir rules) -File -ErrorAction SilentlyContinue | Measure-Object | Select -ExpandProperty Count) 个文件"
Write-Host "  skills/ : $(Get-ChildItem (Join-Path $OpenCodeDir skills) -Directory -ErrorAction SilentlyContinue | Measure-Object | Select -ExpandProperty Count) 个目录"
Write-Host "  commands/: $(Get-ChildItem (Join-Path $OpenCodeDir commands) -File -ErrorAction SilentlyContinue | Measure-Object | Select -ExpandProperty Count) 个文件"

Write-Host ""
Write-Host "============================================"
Write-Host "部署完成。"
Write-Host "Core 内容已链接到 %APPDATA%\OpenCode (agents/rules/skills/commands)"
Write-Host "在新项目中运行 workspace_init 链接 domain 模块。"
Write-Host "============================================"
