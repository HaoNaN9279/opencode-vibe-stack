#!/bin/bash
# 一键部署OpenCode Vibe Coding工具链到Linux/WSL2系统

set -e

STACK_ROOT="${OPCODE_STACK_ROOT:-$(pwd)}"

# 检查Git
if ! command -v git &> /dev/null; then
    echo "错误: Git未安装"
    exit 1
fi

git lfs install 2>/dev/null || true

# 设置环境变量
export OPCODE_STACK_ROOT="$STACK_ROOT"
if [ -f "$HOME/.bashrc" ]; then
    echo "export OPCODE_STACK_ROOT=\"$STACK_ROOT\"" >> "$HOME/.bashrc"
fi

# 创建OpenCode配置目录
OPCODE_CONFIG_DIR="$HOME/.config/opencode/User"
mkdir -p "$OPCODE_CONFIG_DIR"

# 创建符号链接
ln -sfn "$STACK_ROOT/core" "$OPCODE_CONFIG_DIR/core"

# 检查 uv（Python MCP 服务依赖 uvx）
if ! command -v uv &> /dev/null; then
    echo "提示: 建议安装 uv (curl -LsSf https://astral.sh/uv/install.sh | sh)"
    echo "Python MCP 服务依赖 uv/uvx 启动"
fi

echo "部署完成！"
echo "core/ 目录已部署到 User/core/（启动时自动发现）"
echo "domain 模块通过 workspace 文件的 imports 按需加载"
