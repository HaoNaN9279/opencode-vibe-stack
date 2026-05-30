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

function Install-CoreSymlinks {
    param([string]$VibeHome)

    $openCodeConfig = "$env:USERPROFILE\.config\opencode"
    New-Item -ItemType Directory -Force -Path $openCodeConfig | Out-Null

    $symlinkTypes = @("rules", "agents", "commands", "skills", "mcp")

    foreach ($type in $symlinkTypes) {
        $srcDir = "$VibeHome\core\$type"
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
}
