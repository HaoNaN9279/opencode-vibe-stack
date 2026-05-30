# ---- MCP Config Merge ----
# Scans core/mcp/*.json and merges MCP server entries into opencode.json
# with "vibe:core-" prefix for namespace isolation.

function Merge-CoreMcpConfigs {
    param([string]$VibeHome)

    $mcpDir = "$VibeHome\core\mcp"
    if (-not (Test-Path $mcpDir)) { return }

    $jsonFiles = Get-ChildItem "$mcpDir\*.json" -ErrorAction SilentlyContinue
    if (-not $jsonFiles) { return }

    $opencodeConfig = "$env:USERPROFILE\.config\opencode"
    $opencodeJson = "$opencodeConfig\opencode.json"
    if (-not (Test-Path $opencodeJson)) { return }

    $count = 0

    foreach ($jsonFile in $jsonFiles) {
        try {
            $data = Get-Content -Raw $jsonFile.FullName | ConvertFrom-Json
            $mcpBlock = $data.mcp
            if (-not $mcpBlock) { $mcpBlock = $data.mcpServers }
            if (-not $mcpBlock) { continue }

            foreach ($prop in $mcpBlock.PSObject.Properties) {
                $serverName = "vibe:core-$($prop.Name)"

                # Idempotent: skip if already present in opencode.json
                $raw = Get-Content -Raw -Path $opencodeJson
                if ($raw.Contains("`"$serverName`"")) { continue }

                # Serialize server config to single-line JSON
                $configJson = $prop.Value | ConvertTo-Json -Compress -Depth 10

                # ---- Insert into opencode.json mcp block ----
                $lines = Get-Content -Path $opencodeJson
                $newLines = [System.Collections.ArrayList]::new()
                $inMCP = $false
                $mcpDepth = 0
                $inserted = $false
                $foundMcpKey = $false

                foreach ($line in $lines) {
                    if ($inserted) {
                        [void]$newLines.Add($line)
                        continue
                    }

                    # Detect mcp key at any position
                    if ($line -match '^\s*"mcp"\s*:' -or $line -match '^\s*"mcpServers"\s*:') {
                        $foundMcpKey = $true
                    }

                    # Entering mcp block
                    if (-not $inMCP -and ($line -match '^\s*"mcp"\s*:\s*\{' -or $line -match '^\s*"mcpServers"\s*:\s*\{')) {
                        $inMCP = $true
                        $mcpDepth = 1

                        # Handle inline empty mcp object: "mcp": {}
                        if ($line -match '\{.*\}') {
                            $line = [regex]::Replace($line, '\{.*\}', '{')
                            [void]$newLines.Add($line)
                            [void]$newLines.Add("      `"$serverName`": $configJson")
                            [void]$newLines.Add("    }")
                            $inserted = $true
                            continue
                        }
                        [void]$newLines.Add($line)
                        continue
                    }

                    # Inside mcp block: track depth, insert before closing brace
                    if ($inMCP) {
                        $opens = [regex]::Matches($line, '{').Count
                        $closes = [regex]::Matches($line, '}').Count
                        $mcpDepth += $opens - $closes

                        if ($mcpDepth -le 0) {
                            # End of mcp block — insert entry before closing
                            [void]$newLines.Add("      `"$serverName`": $configJson,")
                            $inserted = $true
                        }
                    }
                    elseif ($line.TrimEnd() -match '^\}\s*,?\s*$' -and -not $foundMcpKey) {
                        # No mcp key found at all — inject mcp block before final closing brace
                        [void]$newLines.Add('    "mcp": {')
                        [void]$newLines.Add("      `"$serverName`": $configJson")
                        [void]$newLines.Add('    },')
                        $inserted = $true
                    }

                    [void]$newLines.Add($line)
                }

                if (-not $inserted) { continue }

                $joined = $newLines -join [Environment]::NewLine
                Set-Content -Path $opencodeJson -Value $joined -Encoding UTF8
                $count++
            }
        } catch {
            continue
        }
    }

    if ($count -gt 0) {
        Write-OK "MCP activated ($count servers with vibe:core- prefix)"
    }
}
