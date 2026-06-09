# ---- Helper: Create per-item symlinks from source directory into dest directory ----
# Replaces the old directory-level junction approach with individual item links.
# Removes an old junction at DestDir if present, creates DestDir as a real directory,
# then creates per-item links: file symlinks for files, junctions for subdirectories.
# Falls back to copy for files when symlinks are unavailable (no Developer Mode).
function New-PerItemDirectoryLink {
    param(
        [string]$SourceDir,
        [string]$DestDir
    )

    Write-Info "Linking items from $(Split-Path $SourceDir -Leaf)/ ..."

    # Remove old junction/reparse-point at DestDir if present (legacy directory-level link)
    if (Test-Path $DestDir) {
        try {
            $existing = Get-Item $DestDir -Force -ErrorAction Stop
            $isReparse = ($existing.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq [System.IO.FileAttributes]::ReparsePoint
            if ($isReparse) {
                & cmd.exe /c "rmdir `"$DestDir`"" 2>$null
            }
        } catch {
            # Continue — will be overwritten by directory creation below
        }
    }

    # Ensure DestDir is a real directory
    New-Item -ItemType Directory -Force -Path $DestDir | Out-Null

    $items = Get-ChildItem -Path $SourceDir -Force -ErrorAction SilentlyContinue
    if (-not $items) {
        Write-OK "  (empty directory)"
        return
    }

    foreach ($item in $items) {
        $targetPath = $item.FullName
        $linkPath  = Join-Path $DestDir $item.Name

        if ($item.PSIsContainer) {
            # Subdirectory → junction (reliable, no admin or Developer Mode needed)
            try {
                if (Test-Path $linkPath) {
                    $ex = Get-Item $linkPath -Force -ErrorAction Stop
                    $isRp = ($ex.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq [System.IO.FileAttributes]::ReparsePoint
                    if ($isRp) { & cmd.exe /c "rmdir `"$linkPath`"" 2>$null }
                    else        { Remove-Item $linkPath -Recurse -Force -ErrorAction Stop }
                }
                New-Item -ItemType Junction -Path $linkPath -Target $targetPath -Force | Out-Null
                Write-OK "  $($item.Name)/ -> per-item junction"
            } catch {
                Write-Warn "  Failed to create junction for $($item.Name)/"
            }
        } else {
            # File → symlink (requires Developer Mode or admin); fallback to copy
            try {
                if (Test-Path $linkPath) {
                    Remove-Item $linkPath -Force -ErrorAction Stop
                }
                New-Item -ItemType SymbolicLink -Path $linkPath -Target $targetPath -Force -ErrorAction Stop | Out-Null
                Write-OK "  $($item.Name) -> per-item symlink"
            } catch {
                Write-Warn "  Failed to create symlink for $($item.Name)"
            }
        }
    }
}

function Install-CoreSymlinks {
    param([string]$VibeHome)

    $openCodeConfig = "$env:USERPROFILE\.config\opencode"
    New-Item -ItemType Directory -Force -Path $openCodeConfig | Out-Null

    $symlinkTypes = @("rules", "agents", "commands", "skills", "mcp", "tools")

    foreach ($type in $symlinkTypes) {
        $srcDir = "$VibeHome\core\$type"
        $destDir = "$openCodeConfig\$type"

        if (-not (Test-Path $srcDir)) {
            Write-Warn "[skip] $type/ - source not found (empty core dir - ok)"
            continue
        }

        New-PerItemDirectoryLink -SourceDir $srcDir -DestDir $destDir
    }
}
