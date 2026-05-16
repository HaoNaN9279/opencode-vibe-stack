<#
.SYNOPSIS
创建新的Vibe Coding项目
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,

    [ValidateSet("unity", "unreal", "nodejs", "dcc-plugin", "multi-domain")]
    [string]$Template = "multi-domain",

    [string[]]$Domains = @()
)

$projectPath = Join-Path (Get-Location) $ProjectName
New-Item -ItemType Directory -Path $projectPath | Out-Null

# 复制工作区模板
$templatePath = "$env:OPCODE_STACK_ROOT\workspace-templates\$Template-project"
if (Test-Path $templatePath) {
    Copy-Item "$templatePath\*" $projectPath -Recurse -Force
}

# 初始化Git仓库
Set-Location $projectPath
git init
git add .
git commit -m "Initial commit: $ProjectName"

Write-Host "项目 $ProjectName 创建成功！"
