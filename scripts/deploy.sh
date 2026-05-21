#!/bin/bash
# OpenCode Vibe Coding 工具链部署脚本 - Linux / WSL2
# 逐个链接 core 下的 agents/rules/skills/commands 到 ~/.config/opencode/
# 支持重复执行：自动同步新增、修改和删除的文件
set -e

STACK_ROOT="${OPCODE_STACK_ROOT:-$(pwd)}"
STACK_ROOT="$(realpath "$STACK_ROOT")"
OPCODE_DIR="$HOME/.config/opencode"
CORE_SRC="$STACK_ROOT/core"

# ============================================================
# 工具函数
# ============================================================

# 同步一个文件类别（源目录下的文件 → 目标目录下的同名文件）
# $1: 类型名 (agents/rules/commands)
sync_files() {
    local type="$1"
    local src_dir="$CORE_SRC/$type"
    local dst_dir="$OPCODE_DIR/$type"

    if [ ! -d "$src_dir" ]; then
        return 0
    fi

    mkdir -p "$dst_dir"

    local seen=()

    # 源 → 目标: 创建 / 修正 / 跳过
    for src_file in "$src_dir"/*; do
        [ -e "$src_file" ] || continue
        local name="$(basename "$src_file")"
        local dst_file="$dst_dir/$name"

        seen+=("$name")

        if [ -L "$dst_file" ]; then
            local cur_target="$(readlink "$dst_file")"
            if [ "$cur_target" = "$src_file" ]; then
                continue  # 已存在且正确
            fi
            rm "$dst_file"
        elif [ -e "$dst_file" ]; then
            mv "$dst_file" "${dst_file}.bak.$(date +%Y%m%d%H%M%S)"
        fi

        ln -s "$src_file" "$dst_file"
        echo "  + $type/$name"
    done

    # 目标 → 源反向: 清理过期链接（含断链）
    for dst_file in "$dst_dir"/*; do
        [ -e "$dst_file" ] || [ -L "$dst_file" ] || continue
        local name="$(basename "$dst_file")"
        if [ -L "$dst_file" ]; then
            local target="$(readlink "$dst_file")"
            if [[ "$target" == "$CORE_SRC/$type/"* ]] || [[ "$target" == "$CORE_SRC"/* ]]; then
                # 属于本工具链的链接，检查是否在 seen 中
                local found=0
                for s in "${seen[@]}"; do
                    [ "$s" = "$name" ] && found=1 && break
                done
                if [ "$found" -eq 0 ]; then
                    rm "$dst_file"
                    echo "  - $type/$name (已移除)"
                fi
            fi
        fi
    done
}

# 同步一个技能目录类别（子目录级别的链接）
sync_skill_dirs() {
    local src_dir="$CORE_SRC/skills"
    local dst_dir="$OPCODE_DIR/skills"

    if [ ! -d "$src_dir" ]; then
        return 0
    fi

    mkdir -p "$dst_dir"

    local seen=()

    # 源 → 目标
    for src in "$src_dir"/*/; do
        [ -d "$src" ] || continue
        local name="$(basename "$src")"
        local dst="$dst_dir/$name"

        seen+=("$name")

        if [ -L "$dst" ]; then
            local cur_target="$(readlink "$dst")"
            if [ "$cur_target" = "$src" ]; then
                continue
            fi
            rm "$dst"
        elif [ -e "$dst" ]; then
            mv "$dst" "${dst}.bak.$(date +%Y%m%d%H%M%S)"
        fi

        ln -s "$src" "$dst"
        echo "  + skills/$name/"
    done

    # 反向清理（含断链）
    for dst in "$dst_dir"/*/; do
        [ -d "$dst" ] || [ -L "$dst" ] || continue
        local name="$(basename "$dst")"
        if [ -L "$dst" ]; then
            local target="$(readlink "$dst")"
            if [[ "$target" == "$CORE_SRC/skills/"* ]]; then
                local found=0
                for s in "${seen[@]}"; do
                    [ "$s" = "$name" ] && found=1 && break
                done
                if [ "$found" -eq 0 ]; then
                    rm "$dst"
                    echo "  - skills/$name/ (已移除)"
                fi
            fi
        fi
    done
}

# 同步单个文件
sync_single() {
    local src="$1"
    local dst="$2"
    local label="$3"

    if [ ! -f "$src" ]; then
        return 0
    fi

    mkdir -p "$(dirname "$dst")"

    if [ -L "$dst" ]; then
        local cur="$(readlink "$dst")"
        if [ "$cur" = "$src" ]; then
            return 0
        fi
        rm "$dst"
    elif [ -e "$dst" ]; then
        mv "$dst" "${dst}.bak.$(date +%Y%m%d%H%M%S)"
    fi

    ln -s "$src" "$dst"
    echo "  + $label"
}

# ============================================================
# 1. 环境变量
# ============================================================
echo "============================================"
echo "OpenCode Vibe Stack 部署 (Linux/WSL2)"
echo "============================================"
echo ""

if [ -z "$OPCODE_STACK_ROOT" ] || [ "$OPCODE_STACK_ROOT" != "$STACK_ROOT" ]; then
    export OPCODE_STACK_ROOT="$STACK_ROOT"
    if [ -f "$HOME/.bashrc" ] && ! grep -q "OPCODE_STACK_ROOT" "$HOME/.bashrc"; then
        echo "export OPCODE_STACK_ROOT=\"$OPCODE_STACK_ROOT\"" >> "$HOME/.bashrc"
    fi
    echo ">> OPCODE_STACK_ROOT=$OPCODE_STACK_ROOT"
else
    echo ">> OPCODE_STACK_ROOT 已设置: $OPCODE_STACK_ROOT"
fi

# ============================================================
# 2. 清理旧的 core/ 整体链接（如果存在，从旧版部署遗留）
# ============================================================
OLD_CORE_LINK="$HOME/.config/opencode/User/core"
if [ -L "$OLD_CORE_LINK" ]; then
    echo ">> 清理旧版 core/ 整体链接..."
    rm "$OLD_CORE_LINK"
fi
if [ -d "$HOME/.config/opencode/User" ]; then
    rmdir "$HOME/.config/opencode/User" 2>/dev/null || true
fi

# ============================================================
# 3. 同步链接
# ============================================================
echo ""
echo ">> 同步链接 (core -> ~/.config/opencode/)"

echo "  agents/"
sync_files "agents"

echo "  rules/"
sync_files "rules"

echo "  skills/"
sync_skill_dirs

echo "  commands/"
sync_files "commands"

sync_single \
    "$CORE_SRC/mcp/mcp-config.json" \
    "$OPCODE_DIR/mcp-config.json" \
    "mcp-config.json"

sync_single \
    "$CORE_SRC/domain.config" \
    "$OPCODE_DIR/domain.config" \
    "domain.config"

# ============================================================
# 4. 扫描 domains/ 生成 domain.config
# ============================================================
echo ""
echo ">> 扫描 domains/ 目录..."

python3 - "$STACK_ROOT" << 'PYEOF'
import json, os, sys

STACK_ROOT = sys.argv[1]
DOMAINS_DIR = os.path.join(STACK_ROOT, "domains")

DEFAULT_INDICATORS = {
    "web.nodejs.express":          [{"file": "package.json", "contains": "express"}, {"file": "server.js"}, {"file": "app.js"}],
    "game-engine.unity.csharp-api":[{"file": "*.cs", "contains": "UnityEngine"}, {"file": "*.unity"}, {"dir": "Assets"}, {"dir": "ProjectSettings"}],
    "desktop.csharp.wpf":          [{"file": "*.xaml"}, {"file": "*.csproj", "contains": "WinExe"}, {"file": "App.xaml"}, {"file": "*.cs", "contains": "System.Windows"}],
    "dcc.blender.python-api":      [{"file": "*.py", "contains": "bpy"}, {"file": "__init__.py", "contains": "bl_info"}, {"file": "*.py", "contains": "blender"}],
    "dcc.houdini.vex":             [{"file": "*.vfl"}, {"file": "*.h", "contains": "vop"}, {"file": "*.hip"}],
    "dcc.houdini.hdk":             [{"file": "*.cpp", "contains": "houdini"}, {"file": "*.h", "contains": "HAPI"}, {"file": "CMakeLists.txt", "contains": "houdini"}],
}

TYPE_MAP = {
    "express": "framework", "wpf": "framework", "hdk": "framework",
    "unity": "game-engine", "blender": "dcc-tool", "houdini": "dcc-tool",
    "vex": "language",
}

def get_type(name):
    for key, val in TYPE_MAP.items():
        if key in name:
            return val
    return "unknown"

def get_category(name):
    parts = name.split(".")
    return parts[1] if len(parts) >= 2 else parts[0]

def has_content(domain_path):
    for sub in ["agents", "commands", "rules", "skills"]:
        sub_path = os.path.join(domain_path, sub)
        if os.path.isdir(sub_path) and os.listdir(sub_path):
            return True
    return False

def scan_domains():
    entries = []
    if not os.path.isdir(DOMAINS_DIR):
        return entries

    for root, dirs, files in os.walk(DOMAINS_DIR):
        depth = root[len(DOMAINS_DIR):].count(os.sep)
        if depth == 3:
            rel_path = os.path.relpath(root, DOMAINS_DIR)
            name = rel_path.replace(os.sep, ".")
            entries.append({
                "name": name,
                "path": rel_path,
                "type": get_type(name),
                "category": get_category(name),
                "has_content": has_content(root),
                "indicators": DEFAULT_INDICATORS.get(name, [])
            })
    return entries

entries = scan_domains()
config = {"version": "1.0", "entries": entries}

config_path = os.path.join(STACK_ROOT, "core", "domain.config")
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

content_count = sum(1 for e in entries if e.get("has_content"))
total = len(entries)
print(f"  domain.config 已生成: {total} 个模块, {content_count} 个包含内容, {total - content_count} 个为空壳")
PYEOF

# ============================================================
# 5. 检查可选依赖
# ============================================================
echo ""
echo ">> 检查可选依赖..."

command -v uv &>/dev/null && echo "  uv 已安装" || echo "  提示: 建议安装 uv (用于 Python MCP)"
command -v node &>/dev/null && echo "  node 已安装" || echo "  提示: 建议安装 Node.js (用于 Node.js MCP)"

# ============================================================
# 6. 验证部署
# ============================================================
echo ""
echo ">> 部署验证:"
echo "  agents/ : $(ls -1 "$OPCODE_DIR"/agents/ 2>/dev/null | wc -l) 个文件"
echo "  rules/  : $(ls -1 "$OPCODE_DIR"/rules/ 2>/dev/null | wc -l) 个文件"
echo "  skills/ : $(ls -1d "$OPCODE_DIR"/skills/*/ 2>/dev/null | wc -l) 个目录"
echo "  commands/: $(ls -1 "$OPCODE_DIR"/commands/ 2>/dev/null | wc -l) 个文件"

echo ""
echo "============================================"
echo "部署完成。"
echo "Core 内容已链接到 ~/.config/opencode/ (agents/rules/skills/commands)"
echo "在新项目中运行 workspace_init 链接 domain 模块。"
echo "============================================"
