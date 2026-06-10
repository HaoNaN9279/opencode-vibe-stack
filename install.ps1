# Requirements: PowerShell Admin, uv in PATH

$ErrorActionPreference = "Stop"

# Admin check
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { Write-Host "[ERROR] Run PowerShell as Administrator" -ForegroundColor Red; exit 2 }

$VIBE_STACK_HOME = if ($env:VIBE_STACK_HOME) { $env:VIBE_STACK_HOME } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

# Validate repo
if (-not (Test-Path "$VIBE_STACK_HOME/core/rules/00-global.md")) { Write-Host "[ERROR] Invalid repo" -ForegroundColor Red; exit 1 }

# Check uv
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { Write-Host "[ERROR] uv not found. Install: https://astral.sh/uv/install.ps1" -ForegroundColor Red; exit 1 }

Set-Location $VIBE_STACK_HOME
uv sync
uv run python -m vibe_stack.install
