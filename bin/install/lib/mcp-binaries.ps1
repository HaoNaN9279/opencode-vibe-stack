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
            $rawContent = Get-Content -Raw $jsonFile.FullName
            # Strip JSONC comments (// and /* */) before parsing
            $rawContent = $rawContent -replace '//[^\n]*', ''
            $rawContent = $rawContent -replace '(?s)/\*.*?\*/', ''
            $data = $rawContent | ConvertFrom-Json
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
