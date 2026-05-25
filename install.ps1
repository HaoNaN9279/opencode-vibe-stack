# ============================================================================
# install.ps1 - OpenCode Vibe Stack One-Click Deploy (Windows PowerShell)
#
# Deploys the opencode-vibe-stack configuration management system.
# Creates core symlinks/junctions in ~/.config/opencode/ and installs the CLI.
#
# Usage:
#   irm https://raw.githubusercontent.com/.../install.ps1 | iex
#   # Or clone and run locally:
#   .\install.ps1
#
# Requirements:
#   - Windows 10+ with Developer Mode enabled (for symlinks without admin)
#   - Or run as Administrator
#   - Git must be installed
#
# Environment:
#   $env:VIBE_STACK_HOME     Override install directory (default: ~/.opencode-vibe-stack)
#   $env:VIBE_STACK_REPO     Override git clone URL
#   $env:SKIP_CLONE          Set to 1 to skip git clone
# ============================================================================

param(
    [switch]$SkipClone = $false
)

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

# ---- Detect Setup Mode ----
$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir = if ($scriptPath) { Split-Path -Parent $scriptPath } else { $null }
$isLocalRepo = $false

if ($scriptDir -and (Test-Path "$scriptDir/core/rules/00-global.md") -and (Test-Path "$scriptDir/domains")) {
    $isLocalRepo = $true
    Write-OK "Detected local repo at: $scriptDir"
} else {
    Write-Warn "Running outside repo. Will clone from remote."
}

# ---- Determine VIBE_STACK_HOME ----
if ($env:VIBE_STACK_HOME) {
    $VIBE_STACK_HOME = $env:VIBE_STACK_HOME
} else {
    $VIBE_STACK_HOME = "$env:USERPROFILE\.opencode-vibe-stack"
}
Write-Info "Install directory: $VIBE_STACK_HOME"
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
                # Reparse point (symlink/junction): remove without -Recurse to
                # avoid following the link into the target directory.
                # Use cmd.exe rmdir which safely removes only the reparse point.
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

# ---- Clone / Link Repo ----
if ($SkipClone -or ($env:SKIP_CLONE -eq "1")) {
    Write-Warn "SKIP_CLONE set - skipping repo setup"
} elseif ($isLocalRepo) {
    if ($scriptDir -eq $VIBE_STACK_HOME) {
        Write-OK "Already running from VIBE_STACK_HOME"
    } elseif (Test-Path $VIBE_STACK_HOME) {
        Write-Warn "$VIBE_STACK_HOME already exists, skipping link"
    } else {
        Write-Info "Linking repo -> $VIBE_STACK_HOME"
        New-SafeSymlink -Target $scriptDir -Link $VIBE_STACK_HOME | Out-Null
        Write-OK "Linked"
    }
} else {
    $repoUrl = if ($env:VIBE_STACK_REPO) { $env:VIBE_STACK_REPO } else { "https://github.com/your-org/opencode-vibe-stack.git" }

    if (Test-Path "$VIBE_STACK_HOME/.git") {
        Write-Info "Existing repo found, updating..."
        Push-Location $VIBE_STACK_HOME
        try {
            git pull --ff-only 2>$null
            Write-OK "Updated"
        } catch {
            Write-Warn "Could not update - continuing with existing checkout"
        }
        Pop-Location
    } elseif (Test-Path $VIBE_STACK_HOME) {
        Write-Error_ "$VIBE_STACK_HOME exists but is not a git repo"
        Write-Host "       Remove it or set `$env:VIBE_STACK_HOME to a different path."
        exit 1
    } else {
        Write-Info "Cloning $repoUrl ..."
        git clone $repoUrl $VIBE_STACK_HOME
        Write-OK "Cloned"
    }
}

Write-Host ""

# ---- Create Core Symlinks ----
Write-Bold "[1/3] Creating core symlinks..."

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

    # Check if already correctly linked
    # Note: PS 5.1 (Windows PowerShell) doesn't expose LinkType/Target on
    # directory entries. Skip this optimization -- New-SafeSymlink safely
    # handles re-creation by removing the existing item first.
    if (Test-Path $destDir) {
        try {
            $item = Get-Item $destDir -Force -ErrorAction Stop
            $isReparse = ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq [System.IO.FileAttributes]::ReparsePoint
            if ($isReparse) {
                Write-OK "$type/ -> link exists, will refresh"
            }
        } catch {
            # Can't determine -- let New-SafeSymlink handle it
        }
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

# ---- Update oh-my-openagent.jsonc ----
Write-Bold "[2/3] Updating oh-my-openagent.jsonc..."

$userConfig = "$openCodeConfig\oh-my-openagent.jsonc"

# Ensure config file exists
if (-not (Test-Path $userConfig)) {
    Write-Warn "No oh-my-openagent.jsonc found. Creating minimal config..."
    @'
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json"
}
'@ | Out-File -FilePath $userConfig -Encoding UTF8
    Write-OK "Created $userConfig"
}

# Use Python for JSONC manipulation (check if available)
# On Windows 11, "python" may resolve to the Microsoft Store App Execution
# Alias stub, not a real Python installation. Filter those out.
$pythonCmd = $null
foreach ($candidate in @("python3", "python")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $src = $cmd.Source
        # Skip Microsoft Store stubs (App Installer / WindowsApps paths)
        if ($src -and $src -notmatch '\\WindowsApps\\|AppInstaller') {
            $pythonCmd = $candidate
            break
        }
    }
}

if ($pythonCmd) {
    # Add skills sources
    $skillsPath = $VIBE_STACK_HOME.Replace('\', '/') + "/core/skills"

    $pythonScript = @"
import json, sys, os

config_path = r'$userConfig'.replace('\\', '/')
skills_path = '$skillsPath'

with open(config_path, 'r') as f:
    original = f.read()

lines = []
for line in original.split('\n'):
    in_str = False
    comment_start = -1
    i = 0
    while i < len(line):
        if not in_str and line[i] == '"':
            in_str = True
        elif in_str and line[i] == '\\':
            i += 1
        elif in_str and line[i] == '"':
            in_str = False
        elif not in_str and i + 1 < len(line) and line[i:i+2] == '//':
            comment_start = i
            break
        i += 1
    stripped = line[:comment_start] if comment_start >= 0 else line
    if stripped.strip():
        lines.append(stripped)

clean_json = '\n'.join(lines)
try:
    data = json.loads(clean_json)
except json.JSONDecodeError:
    data = {}

if 'skills' not in data:
    data['skills'] = {}
if 'sources' not in data['skills']:
    data['skills']['sources'] = []

sources = data['skills']['sources']
entry = {'path': skills_path, 'recursive': True}

if not any(s.get('path') == skills_path for s in sources):
    sources.append(entry)
    print(f'    Added skills.sources entry: {skills_path}')
    output = json.dumps(data, indent=2, ensure_ascii=False)
    with open(config_path, 'w') as f:
        f.write(output + '\n')
else:
    print(f'    skills.sources already has: {skills_path}')
"@
    & $pythonCmd -c $pythonScript

    # Add agent definitions
    $agentsPath = $VIBE_STACK_HOME.Replace('\', '/') + "/core/agents/"

    $pythonScript2 = @"
import json, sys

config_path = r'$userConfig'.replace('\\', '/')
agents_path = '$agentsPath'

with open(config_path, 'r') as f:
    original = f.read()

lines = []
for line in original.split('\n'):
    in_str = False
    comment_start = -1
    i = 0
    while i < len(line):
        if not in_str and line[i] == '"':
            in_str = True
        elif in_str and line[i] == '\\':
            i += 1
        elif in_str and line[i] == '"':
            in_str = False
        elif not in_str and i + 1 < len(line) and line[i:i+2] == '//':
            comment_start = i
            break
        i += 1
    stripped = line[:comment_start] if comment_start >= 0 else line
    if stripped.strip():
        lines.append(stripped)

clean_json = '\n'.join(lines)
try:
    data = json.loads(clean_json)
except json.JSONDecodeError:
    data = {}

if 'agent_definitions' not in data:
    data['agent_definitions'] = []

if agents_path not in data['agent_definitions']:
    data['agent_definitions'].append(agents_path)
    print(f'    Added agent_definitions: {agents_path}')

    output = json.dumps(data, indent=2, ensure_ascii=False)
    with open(config_path, 'w') as f:
        f.write(output + '\n')
else:
    print(f'    agent_definitions already has: {agents_path}')
"@
    & $pythonCmd -c $pythonScript2

    Write-OK "Config updated"
} else {
    Write-Warn "python3 not available - skipping oh-my-openagent.jsonc update"
    Write-Warn "   You'll need to manually add skills.sources and agent_definitions"
}

Write-Host ""

# ---- Install CLI Tool ----
Write-Bold "[3/3] Installing CLI tool..."

$cliSrc = "$VIBE_STACK_HOME\bin\vibe-stack"
$cliDestDir = "$env:USERPROFILE\.local\bin"

if (-not (Test-Path $cliDestDir)) {
    New-Item -ItemType Directory -Force -Path $cliDestDir | Out-Null
}

if (Test-Path $cliSrc) {
    # Create a PowerShell wrapper script that calls bash
    $cliWrapperPath = "$cliDestDir\vibe-stack.ps1"
    $cliWrapperContent = @"
# vibe-stack CLI wrapper for Windows
# Requires: Git Bash or WSL bash in PATH
param([string[]]`$args)

`$vibeHome = if (`$env:VIBE_STACK_HOME) { `$env:VIBE_STACK_HOME } else { "`$env:USERPROFILE\.opencode-vibe-stack" }
`$script = Join-Path `$vibeHome "bin\vibe-stack"

# Try bash from Git for Windows, then WSL, then MSYS2
`$bash = `$null
foreach (`$candidate in @("bash", "C:\Program Files\Git\bin\bash.exe", "wsl")) {
    if (Get-Command `$candidate -ErrorAction SilentlyContinue) {
        `$bash = `$candidate
        break
    }
}

if (`$bash -eq `$null) {
    Write-Host "ERROR: bash not found. Install Git for Windows or WSL." -ForegroundColor Red
    exit 1
}

& `$bash `$script @args
"@
    Set-Content -Path $cliWrapperPath -Value $cliWrapperContent -Encoding UTF8
    Write-OK "CLI wrapper installed: $cliWrapperPath"

    # Also try to create a direct symlink if bash is in PATH
    if (Get-Command bash -ErrorAction SilentlyContinue) {
        $cliDest = "$cliDestDir\vibe-stack"
        New-SafeSymlink -Target $cliSrc -Link $cliDest | Out-Null
    }

    # Add to PATH if not present
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$cliDestDir*") {
        Write-Warn "$cliDestDir is not in your user PATH."
        Write-Host "       Add it manually or run:"
        Write-Host "       [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';$cliDestDir', 'User')" -ForegroundColor Cyan
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
Write-Host "     cd ~/.opencode-vibe-stack && git pull" -ForegroundColor Cyan
Write-Host "     vibe-stack core-update" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Location:   $VIBE_STACK_HOME"
Write-Host "  CLI Tool:   $cliDestDir\vibe-stack.ps1"
Write-Host ""
