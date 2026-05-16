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

if [ -d "$STACK_ROOT/platforms/linux" ]; then
    ln -sfn "$STACK_ROOT/platforms/linux" "$OPCODE_CONFIG_DIR/platform"
fi

ln -sfn "$STACK_ROOT/domains" "$OPCODE_CONFIG_DIR/domains"
ln -sfn "$STACK_ROOT/combinations" "$OPCODE_CONFIG_DIR/combinations"

# 配置国内镜像
npm config set registry https://registry.npmmirror.com 2>/dev/null || true
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true

echo "部署完成！请重启OpenCode以应用配置。"
