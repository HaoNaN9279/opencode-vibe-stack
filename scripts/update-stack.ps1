<#
.SYNOPSIS
更新OpenCode Vibe Coding工具链
#>

param(
    [string]$Module = "",
    [string[]]$Modules = @(),
    [switch]$All
)

Set-Location $env:OPCODE_STACK_ROOT

if ($All -or ($Module -eq "" -and $Modules.Count -eq 0)) {
    # 更新所有模块
    git pull origin main
    git lfs pull
} elseif ($Modules.Count -gt 0) {
    # 更新指定模块
    git fetch origin main
    foreach ($mod in $Modules) {
        git checkout origin/main -- "domains/$($mod -replace '\.', '/')/**"
    }
} else {
    # 更新单个模块
    git fetch origin main
    git checkout origin/main -- "domains/$($Module -replace '\.', '/')/**"
}

Write-Host "工具链更新完成！"
