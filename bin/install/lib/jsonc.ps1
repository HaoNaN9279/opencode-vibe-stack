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
    if ($content -notmatch """$Key""") { return 1 }
    
    # Read line by line, find key then closing bracket, insert before it
    $lines = Get-Content -Path $FilePath
    $newLines = [System.Collections.ArrayList]::new()
    $inKey = $false
    $done = $false
    
    foreach ($line in $lines) {
        if (-not $done) {
            if ($line -match """$Key""") { $inKey = $true }
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
