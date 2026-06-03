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

# ---- Check Administrator privileges ----
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    $host.UI.WriteErrorLine("ERROR: This installer requires Administrator privileges to create symlinks.")
    $host.UI.WriteErrorLine("")
    $host.UI.WriteErrorLine("Please re-run PowerShell as Administrator:")
    $host.UI.WriteErrorLine("  Right-click PowerShell -> 'Run as Administrator'")
    $host.UI.WriteErrorLine("  Then navigate to this directory and run: .\install.ps1")
    $host.UI.WriteErrorLine("")
    exit 2
}
Write-OK "Running with Administrator privileges."
Write-Host ""

# ---- Dot-source library modules ----
$libDir = Join-Path $PSScriptRoot "bin\install\lib"
. "$libDir\helpers.ps1"
. "$libDir\symlinks.ps1"
. "$libDir\jsonc.ps1"
. "$libDir\mcp-config.ps1"
. "$libDir\mcp-binaries.ps1"
. "$libDir\cli-install.ps1"

# ---- Determine VIBE_STACK_HOME ----
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

Show-InstallBanner

# ---- [1/4] Create Core Symlinks ----
Write-Bold "[1/4] Creating core symlinks..."
Install-CoreSymlinks -VibeHome $VIBE_STACK_HOME
Write-Host ""

# ---- [2/4] Update configuration files ----
Write-Bold "[2/4] Updating configuration files..."

$openCodeConfig = "$env:USERPROFILE\.config\opencode"
$opencodeJson = "$openCodeConfig\opencode.json"
$rulesGlob = "~/.config/opencode/rules/*.md"

if (-not (Test-Path $opencodeJson)) {
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

# ---- Register core skills in opencode.json ----
$raw = Get-Content -Raw -Path $opencodeJson
if ($raw -match '"skills"\s*:') {
    Add-JsoncNestedArrayValue -FilePath $opencodeJson -ParentKey "skills" -ChildKey "paths" -Value '"skills"'
} else {
    $lines = Get-Content -Path $opencodeJson
    $last = $lines.Count - 1
    $lines[$last - 1] = $lines[$last - 1] + ','
    $lines = $lines[0..($last-1)] + @(
        '  "skills": {',
        '    "paths": ["skills"]',
        '  }',
        '}'
    )
    Set-Content -Path $opencodeJson -Value $lines -Encoding UTF8
}
Write-OK "Registered core skills in skills.paths"
Write-Host ""

# ---- [3/4] Install MCP Binaries ----
Write-Bold "[3/4] Installing MCP binaries..."
Install-McpBinaries -VibeHome $VIBE_STACK_HOME
Write-Host ""

# ---- [4/4] Install CLI Tool ----
Write-Bold "[4/4] Installing CLI tool..."
Install-CliTool -VibeHome $VIBE_STACK_HOME
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
$cliDestDir = "$env:USERPROFILE\.local\bin"
Write-Host "  CLI Tool:   $cliDestDir\vibe-stack.cmd (primary) / .ps1 (PowerShell)"
Write-Host ""
