# ============================================================================
# install.ps1 - OpenCode Vibe Stack One-Click Deploy (Windows PowerShell)
#
# Deploys the opencode-vibe-stack configuration management system.
# Creates core symlinks/junctions in ~/.config/opencode/ and installs the CLI.
#
# Usage:
#   .\install.ps1
#
# VIBE_STACK_HOME is auto-detected as the directory containing this script
# (i.e. the repo root). Override with:
#   $env:VIBE_STACK_HOME = "C:\custom\path"; .\install.ps1
#
# Requirements:
#   - Windows 10+ with Developer Mode enabled (for symlinks without admin)
#   - Or run as Administrator
#   - Git must be installed
#
# Environment:
#   $env:VIBE_STACK_HOME     Override install directory (default: script directory)
# ============================================================================

$ErrorActionPreference = "Stop"

# ---- Helpers ----
function Write-Info  { Write-Host "[i] $args" -ForegroundColor Cyan }
function Write-OK    { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "[warn] $args" -ForegroundColor Yellow }
function Write-Error_ { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Bold  { Write-Host $args -ForegroundColor White }

# ---- Banner ----
Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "     OpenCode Vibe Stack - Windows Installer         " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# ---- Determine VIBE_STACK_HOME ----
# Default to the directory containing this script (the repo root)
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = if ($scriptPath) { Split-Path -Parent $scriptPath } else { $PWD.Path }

if ($env:VIBE_STACK_HOME) {
    $VIBE_STACK_HOME = $env:VIBE_STACK_HOME
} else {
    $VIBE_STACK_HOME = $scriptDir
}

# Verify we're in the repo
if (-not (Test-Path "$VIBE_STACK_HOME/core/rules/00-global.md") -or -not (Test-Path "$VIBE_STACK_HOME/domains")) {
    Write-Error_ "VIBE_STACK_HOME does not appear to be a valid vibe-stack repo: $VIBE_STACK_HOME"
    Write-Host "       Run this script from within the opencode-vibe-stack repository."
    exit 1
}

Write-OK "Repo root: $VIBE_STACK_HOME"
Write-Host ""

# ---- Helper: Create symbolic link (with junction fallback) ----
function New-SafeSymlink {
    param(
        [string]$Target,
        [string]$Link
    )

    # Remove existing if present
    if (Test-Path $Link) {
        try {
            $existing = Get-Item $Link -Force -ErrorAction Stop
            $isReparse = ($existing.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq [System.IO.FileAttributes]::ReparsePoint
            if ($isReparse) {
                & cmd.exe /c "rmdir `"$Link`""
                if ($LASTEXITCODE -ne 0) {
                    throw "rmdir failed with exit code $LASTEXITCODE"
                }
            } else {
                Remove-Item $Link -Recurse -Force -ErrorAction Stop
            }
        } catch {
            Write-Warn "Could not remove existing: $Link"
            return $false
        }
    }

    # Try symlink first
    try {
        New-Item -ItemType SymbolicLink -Path $Link -Target $Target -Force -ErrorAction Stop | Out-Null
        return $true
    } catch {
        # Symlink failed - try junction (directories only)
        if (Test-Path $Target -PathType Container) {
            try {
                New-Item -ItemType Junction -Path $Link -Target $Target -Force -ErrorAction Stop | Out-Null
                Write-Warn "Used Junction instead of Symlink for: $Link"
                return $true
            } catch {
                Write-Warn "Junction also failed for: $Link"
                return $false
            }
        } else {
            Write-Warn "Cannot create link for: $Link (file symlink requires admin or Developer Mode)"
            return $false
        }
    }
}

# ---- Create Core Symlinks ----
Write-Bold "[1/4] Creating core symlinks..."

$openCodeConfig = "$env:USERPROFILE\.config\opencode"
New-Item -ItemType Directory -Force -Path $openCodeConfig | Out-Null

$symlinkTypes = @("rules", "agents", "commands", "skills", "mcp")

foreach ($type in $symlinkTypes) {
    $srcDir = "$VIBE_STACK_HOME\core\$type"
    $destDir = "$openCodeConfig\$type"

    if (-not (Test-Path $srcDir)) {
        Write-Warn "[skip] $type/ - source not found (empty core dir - ok)"
        continue
    }

    Write-Info "Linking $type/ ..."
    $success = New-SafeSymlink -Target $srcDir -Link $destDir
    if ($success) {
        Write-OK "$type/ -> $srcDir"
    } else {
        Write-Warn "Failed to create symlink for $type/"
    }
}

Write-Host ""

# ---- Update configuration files ----
Write-Bold "[2/4] Updating configuration files..."

# ---- JSONC helpers (text-based, preserves comments, formatting, and all other content) ----

# Check if a value string exists in a JSONC file
function Test-JsoncValue {
    param([string]$FilePath, [string]$Value)
    if (-not (Test-Path $FilePath)) { return $false }
    $content = Get-Content -Raw -Path $FilePath -ErrorAction SilentlyContinue
    if (-not $content) { return $false }
    return $content.Contains($Value)
}

# Add a value to a JSON array by key (inserts before closing bracket).
# Returns: 0=added, 1=key not found, 2=already exists
function Add-JsoncArrayValue {
    param([string]$FilePath, [string]$Key, [string]$Value)
    
    if (-not (Test-Path $FilePath)) { return 1 }
    
    # Already exists?
    if (Test-JsoncValue $FilePath $Value) { return 2 }
    
    $content = Get-Content -Raw -Path $FilePath
    # Key exists?
    if ($content -notmatch """$Key""") { return 1 }
    
    # Read line by line, find key then closing bracket, insert before it
    $lines = Get-Content -Path $FilePath
    $newLines = [System.Collections.ArrayList]::new()
    $inKey = $false
    $done = $false
    
    foreach ($line in $lines) {
        if (-not $done) {
            if ($line -match """$Key""") { $inKey = $true }
            if ($inKey -and ($line -match '^\s*\]\s*,?\s*$')) {
                [void]$newLines.Add("    ""$Value"",")
                $done = $true
            }
        }
        [void]$newLines.Add($line)
    }
    
    # Fix trailing comma on the entry just before our insertion (the original last entry)
    $joined = $newLines -join [Environment]::NewLine
    Set-Content -Path $FilePath -Value $joined -Encoding UTF8
    return 0
}

# -- 2a. Update opencode.json with core rules as instructions --
$opencodeJson = "$openCodeConfig\opencode.json"
$rulesGlob = "rules/*.md"

if (-not (Test-Path $opencodeJson)) {
    # Create new file from scratch
    $initial = "{" + [Environment]::NewLine +
               "  `"`$schema`": `"https://opencode.ai/config.json`"," + [Environment]::NewLine +
               "  `"instructions`": [" + [Environment]::NewLine +
               "    `"$rulesGlob`"" + [Environment]::NewLine +
               "  ]" + [Environment]::NewLine +
               "}" + [Environment]::NewLine
    Set-Content -Path $opencodeJson -Value $initial -Encoding UTF8 -NoNewline
    Write-OK "Created $opencodeJson with instructions: $rulesGlob"
}
else {
    $result = Add-JsoncArrayValue -FilePath $opencodeJson -Key "instructions" -Value $rulesGlob
    switch ($result) {
        0 { Write-OK "Added instructions: $rulesGlob" }
        2 { Write-OK "instructions already has: $rulesGlob" }
        1 { Write-Warn "instructions key not found in $opencodeJson — skipping" }
    }
}



Write-Host ""

# ---- Install MCP Binaries ----
#
# Scans $VibeHome\domains\*\mcp\*.json for MCP configs with "release" metadata,
# and downloads the pre-built binary from GitHub Releases.
# Configs without "release" are skipped (binary expected to be already present).
function Install-McpBinaries {
    param([string]$VibeHome)

    # Detect platform key matching the release.asset map
    $platformKey = if ($IsLinux) { "linux" }
                   elseif ($IsMacOS) { "darwin" }
                   else { "windows" }

    $foundAny = $false
    $jsonPattern = Join-Path $VibeHome "domains\*\mcp\*.json"

    $jsonFiles = Get-ChildItem -Path $jsonPattern -ErrorAction SilentlyContinue |
                 Where-Object { $_.Name -ne "README.md" }

    foreach ($jsonFile in $jsonFiles) {
        try {
            $data = Get-Content -Raw $jsonFile.FullName | ConvertFrom-Json
        } catch {
            continue
        }

        $mcpBlock = $data.mcp
        if (-not $mcpBlock) { $mcpBlock = $data.mcpServers }
        if (-not $mcpBlock) { continue }

        foreach ($prop in $mcpBlock.PSObject.Properties) {
            $name = $prop.Name
            $cfg = $prop.Value

            if (-not $cfg.release) {
                # Config without release metadata — skip (binary assumed already in repo)
                continue
            }

            # Resolve binary path from command array
            $cmd = $cfg.command
            if (-not $cmd -or $cmd.Count -eq 0) { continue }
            $binaryPath = $cmd[0].Replace('${VIBE_STACK_HOME}', $VibeHome)

            # Skip if already installed
            if (Test-Path $binaryPath -PathType Leaf) {
                Write-Host "  [OK] $name` — binary already installed at $binaryPath" -ForegroundColor Green
                $foundAny = $true
                continue
            }

            # Determine asset name for this platform
            $assetName = $cfg.release.asset.$platformKey
            if (-not $assetName) {
                Write-Warn "$name`: no asset defined for platform '$platformKey'"
                continue
            }

            $repo = $cfg.release.repo
            if (-not $repo) {
                Write-Warn "$name`: missing 'repo' in release metadata"
                continue
            }

            $url = "https://github.com/$repo/releases/latest/download/$assetName"
            $binaryDir = Split-Path -Parent $binaryPath

            Write-Info "$name`: downloading $assetName ..."

            if (-not (Test-Path $binaryDir)) {
                New-Item -ItemType Directory -Force -Path $binaryDir | Out-Null
            }

            try {
                Invoke-WebRequest -Uri $url -OutFile $binaryPath -ErrorAction Stop
                # Set executable attribute (not strictly needed on Windows, but harmless)
                Write-Host "    [OK] $assetName installed -> $binaryPath" -ForegroundColor Green
                $foundAny = $true
            } catch {
                Write-Warn "Failed to download $assetName`: $($_.Exception.Message)"
                Write-Host "       URL: $url"
                # Clean up partial download
                if (Test-Path $binaryPath) { Remove-Item $binaryPath -Force -ErrorAction SilentlyContinue }
            }
        }
    }

    if (-not $foundAny) {
        Write-Info "No MCP binaries to download (all already installed or no release metadata)."
    }
}

Write-Bold "[3/4] Installing MCP binaries..."
Write-Host ""
Install-McpBinaries -VibeHome $VIBE_STACK_HOME
Write-Host ""

# ---- Install CLI Tool ----
Write-Bold "[4/4] Installing CLI tool..."

$cliSrc = "$VIBE_STACK_HOME\bin\vibe-stack"
$cliDestDir = "$env:USERPROFILE\.local\bin"

if (-not (Test-Path $cliDestDir)) {
    New-Item -ItemType Directory -Force -Path $cliDestDir | Out-Null
}

if (Test-Path $cliSrc) {
    # ---- 3a. Create vibe-stack.cmd (primary entry point for Windows) ----
    # Windows uses PATHEXT (.COM;.EXE;.BAT;.CMD) to discover executables.
    # A .cmd wrapper is the standard pattern (npm, pip, etc. all use it).
    $cliCmdPath = "$cliDestDir\vibe-stack.cmd"

    $cliCmdContent = @'
@echo off
setlocal enabledelayedexpansion

set "VIBE_STACK_HOME=%VIBE_STACK_HOME%"
if "%VIBE_STACK_HOME%"=="" set "VIBE_STACK_HOME=__VIBE_STACK_HOME__"

set "VIBE_SCRIPT=!VIBE_STACK_HOME!\bin\vibe-stack"

:: Find bash: Git for Windows, then MSYS2, then System
set "BASH="
for %%d in (
    "C:\Program Files\Git\bin"
    "C:\Program Files\Git\usr\bin"
    "C:\msys64\usr\bin"
    "%ProgramFiles%\Git\bin"
    "%ProgramFiles%\Git\usr\bin"
    "%LocalAppData%\Programs\Git\bin"
) do (
    if "!BASH!"=="" (
        if exist "%%~d\bash.exe" set "BASH=%%~d\bash.exe"
    )
)

:: Fallback: check PATH for bash
if "!BASH!"=="" (
    for %%c in (bash.exe) do (
        if "!BASH!"=="" set "BASH=%%~$PATH:c"
    )
)

if "!BASH!"=="" (
    echo [ERROR] bash not found. Install Git for Windows ^(https://git-scm.com^) or WSL.
    exit /b 1
)

:: Convert backslashes to forward slashes for bash compatibility
set "VIBE_SCRIPT=!VIBE_SCRIPT:\=/!"

:: Pass arguments explicitly (up to 9) for compatibility with PowerShell invocation
"!BASH!" "!VIBE_SCRIPT!" %*
'@
    $cliCmdContent = $cliCmdContent -replace '__VIBE_STACK_HOME__', $VIBE_STACK_HOME
    Set-Content -Path $cliCmdPath -Value $cliCmdContent -Encoding ASCII
    Write-OK "CLI .cmd wrapper installed: $cliCmdPath"

    # ---- 3b. Create vibe-stack.ps1 (PowerShell wrapper, for pwsh users) ----
    $cliPs1Path = "$cliDestDir\vibe-stack.ps1"
    $cliPs1Content = @'
# vibe-stack CLI wrapper for Windows PowerShell
# Requires: Git Bash or WSL bash in PATH
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$PassThruArgs)

$vibeHome = if ($env:VIBE_STACK_HOME) { $env:VIBE_STACK_HOME } else { "__VIBE_STACK_HOME__" }
$vibeScript = (Join-Path $vibeHome "bin\vibe-stack") -replace '\\', '/'

# Search for bash: Git for Windows -> MSYS2 -> WSL -> PATH fallback
$bash = $null
$searchPaths = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files\Git\usr\bin\bash.exe",
    "C:\msys64\usr\bin\bash.exe",
    "$env:ProgramFiles\Git\bin\bash.exe",
    "$env:ProgramFiles\Git\usr\bin\bash.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
)
foreach ($p in $searchPaths) {
    $resolved = $ExecutionContext.InvokeCommand.ExpandString($p)
    if (Test-Path $resolved -PathType Leaf) {
        $bash = $resolved
        break
    }
}
if (-not $bash) {
    $bash = (Get-Command bash -ErrorAction SilentlyContinue).Source
}

if (-not $bash) {
    Write-Host "[ERROR] bash not found. Install Git for Windows (https://git-scm.com) or WSL." -ForegroundColor Red
    exit 1
}

# Ensure the bash script exists
if (-not (Test-Path $vibeScript)) {
    Write-Host "[ERROR] vibe-stack script not found at: $vibeScript" -ForegroundColor Red
    Write-Host "        Run 'git pull' in $vibeHome to update." -ForegroundColor Yellow
    exit 1
}

& $bash $vibeScript @PassThruArgs
'@
    $cliPs1Content = $cliPs1Content -replace '__VIBE_STACK_HOME__', $VIBE_STACK_HOME
    Set-Content -Path $cliPs1Path -Value $cliPs1Content -Encoding UTF8
    Write-OK "CLI .ps1 wrapper installed: $cliPs1Path"

    # ---- 3c. Add ~/.local/bin to user PATH (for real this time) ----
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $userPath) { $userPath = "" }
    if ($userPath -notlike "*$cliDestDir*") {
        try {
            $newUserPath = if ($userPath) { "$userPath;$cliDestDir" } else { $cliDestDir }
            [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
            Write-OK "Added to user PATH: $cliDestDir"

            # Also update PATH for the current session so vibe-stack works immediately
            if ($env:Path -notlike "*$cliDestDir*") {
                $env:Path = "$env:Path;$cliDestDir"
            }
        } catch {
            Write-Warn "Could not update user PATH automatically."
            Write-Host "       Add it manually:"
            Write-Host "       [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';$cliDestDir', 'User')" -ForegroundColor Cyan
        }
    } else {
        Write-OK "$cliDestDir already in user PATH"
    }
} else {
    Write-Warn "CLI script not found at $cliSrc"
    Write-Host "       Make sure you have the latest version of opencode-vibe-stack."
}

Write-Host ""

# ---- Success ----
Write-Host "======================================================" -ForegroundColor Green
Write-Host "          > Installation Complete!                   " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Next Steps:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Verify installation:"
Write-Host "     vibe-stack list" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Activate domains in a project:"
Write-Host "     cd your-project\" -ForegroundColor Cyan
Write-Host "     vibe-stack activate game-dev/unity" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Check active domains:"
Write-Host "     vibe-stack status" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Update the stack later:"
Write-Host "     cd $VIBE_STACK_HOME && git pull" -ForegroundColor Cyan
Write-Host "     vibe-stack core-update" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Location:   $VIBE_STACK_HOME"
Write-Host "  CLI Tool:   $cliDestDir\vibe-stack.cmd (primary) / .ps1 (PowerShell)"
Write-Host ""
