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
        # Calls `uv run python -m vibe_stack.cli` — no bash dependency.
        $cliCmdPath = "$cliDestDir\vibe-stack.cmd"

        $cliCmdContent = '@'
@echo off
setlocal

set "VIBE_STACK_HOME=%VIBE_STACK_HOME%"
if "%VIBE_STACK_HOME%"=="" set "VIBE_STACK_HOME=__VIBE_STACK_HOME__"

cd /d "%VIBE_STACK_HOME%"

uv run python -m vibe_stack.cli %*

endlocal
'@
        $cliCmdContent = $cliCmdContent -replace '__VIBE_STACK_HOME__', $VibeHome
        Set-Content -Path $cliCmdPath -Value $cliCmdContent -Encoding ASCII
        Write-OK "CLI .cmd wrapper installed: $cliCmdPath"

        # ---- 3b. Create vibe-stack.ps1 (PowerShell wrapper, for pwsh users) ----
        # Requires: uv and Python installed and available in PATH.
        $cliPs1Path = "$cliDestDir\vibe-stack.ps1"
        $cliPs1Content = @'
param([Parameter(ValueFromRemainingArguments=$true)][string[]]$PassThruArgs)
$vibeHome = if ($env:VIBE_STACK_HOME) { $env:VIBE_STACK_HOME } else { Join-Path $PSScriptRoot ".." }
Set-Location $vibeHome
uv run python -m vibe_stack.cli @PassThruArgs
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
