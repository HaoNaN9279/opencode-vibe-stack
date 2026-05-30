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
    if (-not $content.Contains('"' + $Key + '"')) { return 1 }
    
    # Read line by line, find key then closing bracket, insert before it
    $lines = Get-Content -Path $FilePath
    $newLines = [System.Collections.ArrayList]::new()
    $inKey = $false
    $done = $false
    
    foreach ($line in $lines) {
        if (-not $done) {
            if ($line.Contains('"' + $Key + '"')) { $inKey = $true }
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

# Add a value to a nested JSON array by parent key and child key (e.g. skills.paths).
# Returns: 0=added, 1=key not found, 2=already exists
function Add-JsoncNestedArrayValue {
    param([string]$FilePath, [string]$ParentKey, [string]$ChildKey, [string]$Value)
    
    if (-not (Test-Path $FilePath)) { return 1 }
    
    # Already exists?
    if (Test-JsoncValue $FilePath $Value) { return 2 }
    
    $content = Get-Content -Raw -Path $FilePath
    # ParentKey exists?
    if (-not $content.Contains('"' + $ParentKey + '"')) { return 1 }
    
    $lines = Get-Content -Path $FilePath
    $newLines = [System.Collections.ArrayList]::new()
    $inParent = $false
    $inChild = $false
    $parentDepth = 0
    $childFound = $false
    $done = $false
    
    foreach ($line in $lines) {
        if (-not $done) {
            # Enter parent scope when ParentKey is found
            if (-not $inParent -and $line.Contains('"' + $ParentKey + '"')) {
                $inParent = $true
                $parentDepth = 0
            }
            
            if ($inParent) {
                # Track brace depth in parent scope
                $braceDelta = 0
                foreach ($c in $line.ToCharArray()) {
                    if ($c -eq '{') { $braceDelta++ }
                    if ($c -eq '}') { $braceDelta-- }
                }
                $parentDepth += $braceDelta
                
                # Look for ChildKey inside parent scope (depth > 0 means inside parent)
                if (-not $childFound -and $line.Contains('"' + $ChildKey + '"') -and $parentDepth -gt 0) {
                    $childFound = $true
                    $inChild = $true
                    
                    # Handle inline empty array: "paths": []
                    if ($line -match '\[\s*\]') {
                        $indent = $line.Length - $line.TrimStart().Length
                        [void]$newLines.Add((" " * $indent) + '"' + $ChildKey + '": [')
                        [void]$newLines.Add((" " * ($indent + 2)) + '"' + $Value + '"')
                        [void]$newLines.Add((" " * $indent) + '],')
                        $done = $true
                        continue
                    }
                }
                
                if ($inChild) {
                    # Insert value before closing bracket of child array
                    if ($line -match '^\s*\]\s*,?\s*$') {
                        $indent = $line.Length - $line.TrimStart().Length
                        [void]$newLines.Add((" " * ($indent + 2)) + '"' + $Value + '",')
                        $done = $true
                    }
                } elseif ($parentDepth -eq 0 -and -not $done -and $line -match '^\s*\}') {
                    # Parent closing brace and child key not found — insert child key structure
                    $indent = $line.Length - $line.TrimStart().Length
                    [void]$newLines.Add((" " * ($indent + 2)) + '"' + $ChildKey + '": [')
                    [void]$newLines.Add((" " * ($indent + 4)) + '"' + $Value + '"')
                    [void]$newLines.Add((" " * ($indent + 2)) + '],')
                    $done = $true
                }
            }
        }
        [void]$newLines.Add($line)
    }
    
    $joined = $newLines -join [Environment]::NewLine
    Set-Content -Path $FilePath -Value $joined -Encoding UTF8
    return 0
}

# Remove a value from a nested JSON array by parent key and child key.
# Returns: 0=removed, 1=not found
function Remove-JsoncNestedArrayValue {
    param([string]$FilePath, [string]$ParentKey, [string]$ChildKey, [string]$Value)
    
    if (-not (Test-Path $FilePath)) { return 1 }
    
    # Doesn't exist?
    if (-not (Test-JsoncValue $FilePath $Value)) { return 1 }
    
    $lines = Get-Content -Path $FilePath
    $newLines = [System.Collections.ArrayList]::new()
    $inParent = $false
    $inChild = $false
    $parentDepth = 0
    $childFound = $false
    $removed = $false
    
    foreach ($line in $lines) {
        if (-not $removed) {
            # Enter parent scope when ParentKey is found
            if (-not $inParent -and $line.Contains('"' + $ParentKey + '"')) {
                $inParent = $true
                $parentDepth = 0
            }
            
            if ($inParent) {
                # Track brace depth in parent scope
                $braceDelta = 0
                foreach ($c in $line.ToCharArray()) {
                    if ($c -eq '{') { $braceDelta++ }
                    if ($c -eq '}') { $braceDelta-- }
                }
                $parentDepth += $braceDelta
                
                # Look for ChildKey inside parent scope
                if (-not $childFound -and $line.Contains('"' + $ChildKey + '"') -and $parentDepth -gt 0) {
                    $childFound = $true
                    $inChild = $true
                }
                
                if ($inChild) {
                    # Match line that is exactly the value (with optional trailing comma)
                    $trimmed = $line.Trim()
                    $quotedVal = '"' + $Value + '"'
                    if ($trimmed -eq $quotedVal -or $trimmed -eq ($quotedVal + ',')) {
                        $removed = $true
                        continue  # Skip this line (remove it)
                    }
                }
            }
        }
        [void]$newLines.Add($line)
    }
    
    if (-not $removed) { return 1 }
    
    $joined = $newLines -join [Environment]::NewLine
    Set-Content -Path $FilePath -Value $joined -Encoding UTF8
    return 0
}
