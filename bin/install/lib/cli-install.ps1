# ---- Install CLI Tool ----

function Install-CliTool {
    param([string]$VibeHome)

    $cliSrc = "$VibeHome\bin\vibe-stack\vibe-stack"
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

set "VIBE_SCRIPT=!VIBE_STACK_HOME!\bin\vibe-stack\vibe-stack"

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
        $cliCmdContent = $cliCmdContent -replace '__VIBE_STACK_HOME__', $VibeHome
        Set-Content -Path $cliCmdPath -Value $cliCmdContent -Encoding ASCII
        Write-OK "CLI .cmd wrapper installed: $cliCmdPath"

        # ---- 3b. Create vibe-stack.ps1 (PowerShell wrapper, for pwsh users) ----
        $cliPs1Path = "$cliDestDir\vibe-stack.ps1"
        $cliPs1Content = @'
# vibe-stack CLI wrapper for Windows PowerShell
# Requires: Git Bash or WSL bash in PATH
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$PassThruArgs)

$vibeHome = if ($env:VIBE_STACK_HOME) { $env:VIBE_STACK_HOME } else { "__VIBE_STACK_HOME__" }
$vibeScript = (Join-Path $vibeHome "bin\vibe-stack\vibe-stack") -replace '\\', '/'

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
        $cliPs1Content = $cliPs1Content -replace '__VIBE_STACK_HOME__', $VibeHome
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
}
