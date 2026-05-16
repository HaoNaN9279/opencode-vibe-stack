<#
.SYNOPSIS
一键部署OpenCode Vibe Coding工具链到Windows系统
#>

param(
    [string]$StackRoot = $PWD.Path
)

# 1. 检查Git和Git LFS
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git未安装，请先安装Git"
    exit 1
}

git lfs install

# 2. 设置环境变量
$env:OPCODE_STACK_ROOT = $StackRoot
[Environment]::SetEnvironmentVariable("OPCODE_STACK_ROOT", $env:OPCODE_STACK_ROOT, "User")

# 3. 创建符号链接
$opcodeConfigDir = [Environment]::GetFolderPath("ApplicationData") + "\OpenCode\User"
if (-not (Test-Path $opcodeConfigDir)) {
    New-Item -ItemType Directory -Path $opcodeConfigDir | Out-Null
}

# 链接核心配置
New-Item -ItemType SymbolicLink -Path "$opcodeConfigDir\core" -Target "$env:OPCODE_STACK_ROOT\core" -Force

# 链接平台特定配置
New-Item -ItemType SymbolicLink -Path "$opcodeConfigDir\platforms\windows" -Target "$env:OPCODE_STACK_ROOT\platforms\windows" -Force

# 链接领域配置
New-Item -ItemType SymbolicLink -Path "$opcodeConfigDir\domains" -Target "$env:OPCODE_STACK_ROOT\domains" -Force

# 链接组合包配置
New-Item -ItemType SymbolicLink -Path "$opcodeConfigDir\combinations" -Target "$env:OPCODE_STACK_ROOT\combinations" -Force

# 4. 配置国内镜像
Write-Host "配置国内镜像..."
npm config set registry https://registry.npmmirror.com
dotnet nuget add source https://nuget.cdn.azure.cn/v3/index.json --name "Azure China"

# 5. 验证安装
Write-Host "验证安装..."
opencode --version
opencode mcp list

Write-Host "部署完成！请重启OpenCode以应用配置。"
