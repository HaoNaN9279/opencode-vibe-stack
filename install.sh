#!/usr/bin/env bash
# ============================================================================
# install.sh - OpenCode Vibe Stack One-Click Deploy (Linux / macOS)
#
# Deploys the opencode-vibe-stack configuration management system.
# Creates core symlinks in ~/.config/opencode/ and installs the CLI tool.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
#   # Or clone and run locally:
#   ./install.sh
#
# Environment:
#   VIBE_STACK_HOME     Override install directory (default: ~/.opencode-vibe-stack)
#   VIBE_STACK_REPO     Override git clone URL
#   SKIP_CLONE=1        Skip git clone (use if already in repo or pre-installed)
# ============================================================================
set -euo pipefail

# ---- Colors (safe for non-TTY) ----
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; NC=''
fi

# ---- Banner ----
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     OpenCode Vibe Stack - One-Click Installer       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ---- Detect Setup Mode ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
IS_LOCAL_REPO=false

# Check if we're running from inside the repo
if [ -f "$REPO_ROOT/core/rules/00-global.md" ] && [ -d "$REPO_ROOT/domains" ]; then
    IS_LOCAL_REPO=true
    echo -e "${GREEN}[✓]${NC} Detected local repo at: $REPO_ROOT"
else
    echo -e "${YELLOW}[!]${NC} Running outside repo. Will clone from remote."
fi

# ---- Determine VIBE_STACK_HOME ----
VIBE_STACK_HOME="${VIBE_STACK_HOME:-$HOME/.opencode-vibe-stack}"
echo -e "${CYAN}[i]${NC} Install directory: ${BOLD}$VIBE_STACK_HOME${NC}"
echo ""

# ---- Clone / Link Repo ----
if [ "${SKIP_CLONE:-0}" = "1" ]; then
    echo -e "${YELLOW}[!]${NC} SKIP_CLONE=1 - skipping repo setup"
elif [ "$IS_LOCAL_REPO" = true ]; then
    # Running from the repo itself
    if [ "$REPO_ROOT" = "$VIBE_STACK_HOME" ]; then
        echo -e "${GREEN}[✓]${NC} Already running from VIBE_STACK_HOME"
    elif [ -e "$VIBE_STACK_HOME" ]; then
        echo -e "${YELLOW}[!]${NC} $VIBE_STACK_HOME already exists, skipping link"
        echo -e "       To update: cd $VIBE_STACK_HOME && git pull"
    else
        echo -e "${CYAN}[i]${NC} Linking repo -> $VIBE_STACK_HOME"
        ln -sf "$REPO_ROOT" "$VIBE_STACK_HOME"
        echo -e "${GREEN}[✓]${NC} Linked"
    fi
else
    # Clone from remote
    REPO_URL="${VIBE_STACK_REPO:-https://github.com/your-org/opencode-vibe-stack.git}"

    if [ -d "$VIBE_STACK_HOME/.git" ]; then
        echo -e "${CYAN}[i]${NC} Existing repo found, updating..."
        git -C "$VIBE_STACK_HOME" pull --ff-only 2>/dev/null || {
            echo -e "${YELLOW}[!]${NC} Could not update - continuing with existing checkout"
        }
        echo -e "${GREEN}[✓]${NC} Updated"
    elif [ -e "$VIBE_STACK_HOME" ]; then
        echo -e "${RED}[✗]${NC} $VIBE_STACK_HOME exists but is not a git repo"
        echo "       Remove it or set VIBE_STACK_HOME to a different path."
        exit 1
    else
        echo -e "${CYAN}[i]${NC} Cloning $REPO_URL ..."
        git clone "$REPO_URL" "$VIBE_STACK_HOME"
        echo -e "${GREEN}[✓]${NC} Cloned"
    fi
fi

echo ""

# ---- Create Core Symlinks ----
echo -e "${BOLD}[1/3] Creating core symlinks...${NC}"

OPENCODE_CONFIG="$HOME/.config/opencode"
mkdir -p "$OPENCODE_CONFIG"

SYMLINK_TYPES=("rules" "agents" "commands" "skills" "mcp")

for type in "${SYMLINK_TYPES[@]}"; do
    src_dir="$VIBE_STACK_HOME/core/$type"
    dest_dir="$OPENCODE_CONFIG/$type"

    # Check if source exists
    if [ ! -d "$src_dir" ]; then
        echo -e "  ${YELLOW}[skip]${NC} $type/ - source not found (empty core dir - ok)"
        continue
    fi

    # Check if already correctly linked
    if [ -L "$dest_dir" ]; then
        current_target="$(readlink "$dest_dir")"
        if [ "$current_target" = "$src_dir" ]; then
            echo -e "  ${GREEN}[OK]${NC} $type/ -> already linked"
            continue
        fi
    fi

    # Remove existing (file, dir, or wrong symlink)
    if [ -e "$dest_dir" ] || [ -L "$dest_dir" ]; then
        echo -e "  ${YELLOW}[!]${NC} Removing existing $type/ ..."
        rm -rf "$dest_dir"
    fi

    # Create symlink
    ln -sf "$src_dir" "$dest_dir"
    echo -e "  ${GREEN}[OK]${NC} $type/ -> $src_dir"
done

echo ""

# ---- Update oh-my-openagent.jsonc ----
echo -e "${BOLD}[2/3] Updating oh-my-openagent.jsonc...${NC}"

USER_CONFIG="$OPENCODE_CONFIG/oh-my-openagent.jsonc"

# Ensure config file exists
if [ ! -f "$USER_CONFIG" ]; then
    echo -e "  ${YELLOW}[!]${NC} No oh-my-openagent.jsonc found. Creating minimal config..."
    cat > "$USER_CONFIG" << 'JSONCEOF'
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/oh-my-opencode.schema.json"
}
JSONCEOF
    echo -e "  ${GREEN}[OK]${NC} Created $USER_CONFIG"
fi

# Add skills sources (for core skills)
add_skills_source() {
    local config_file="$1"
    local skills_path="$2"

    # Use python3 for robust JSONC manipulation
    if command -v python3 &>/dev/null; then
        python3 - "$config_file" "$skills_path" << 'PYEOF'
import json, sys, os

config_path = sys.argv[1]
skills_path = sys.argv[2]

with open(config_path, 'r') as f:
    original = f.read()

# Strip // comments to parse as JSON
lines = []
for line in original.split('\n'):
    in_str = False
    comment_start = -1
    i = 0
    while i < len(line):
        if not in_str and line[i] == '"':
            in_str = True
        elif in_str and line[i] == '\\':
            i += 1
        elif in_str and line[i] == '"':
            in_str = False
        elif not in_str and i + 1 < len(line) and line[i:i+2] == '//':
            comment_start = i
            break
        i += 1
    stripped = line[:comment_start] if comment_start >= 0 else line
    if stripped.strip():
        lines.append(stripped)

clean_json = '\n'.join(lines)
try:
    data = json.loads(clean_json)
except json.JSONDecodeError:
    data = {}

# Ensure skills.sources exists
if 'skills' not in data:
    data['skills'] = {}
if 'sources' not in data['skills']:
    data['skills']['sources'] = []

sources = data['skills']['sources']
entry = {'path': skills_path, 'recursive': True}

if not any(s.get('path') == skills_path for s in sources):
    sources.append(entry)
    print(f'    Added skills.sources entry: {skills_path}')

    # Write back - json.dumps includes $schema if it was in the original
    output = json.dumps(data, indent=2, ensure_ascii=False)
    with open(config_path, 'w') as f:
        f.write(output + '\n')
else:
    print(f'    skills.sources already has: {skills_path}')
PYEOF
    else
        echo -e "  ${YELLOW}[warn]${NC} python3 not available - skipping skills config"
    fi
}

# Add agent definitions (for core agents)
add_agent_defs() {
    local config_file="$1"
    local agents_path="$2"

    if command -v python3 &>/dev/null; then
        python3 - "$config_file" "$agents_path" << 'PYEOF'
import json, sys

config_path = sys.argv[1]
agents_path = sys.argv[2]

with open(config_path, 'r') as f:
    original = f.read()

lines = []
for line in original.split('\n'):
    in_str = False
    comment_start = -1
    i = 0
    while i < len(line):
        if not in_str and line[i] == '"':
            in_str = True
        elif in_str and line[i] == '\\':
            i += 1
        elif in_str and line[i] == '"':
            in_str = False
        elif not in_str and i + 1 < len(line) and line[i:i+2] == '//':
            comment_start = i
            break
        i += 1
    stripped = line[:comment_start] if comment_start >= 0 else line
    if stripped.strip():
        lines.append(stripped)

clean_json = '\n'.join(lines)
try:
    data = json.loads(clean_json)
except json.JSONDecodeError:
    data = {}

if 'agent_definitions' not in data:
    data['agent_definitions'] = []

if agents_path not in data['agent_definitions']:
    data['agent_definitions'].append(agents_path)
    print(f'    Added agent_definitions: {agents_path}')

    output = json.dumps(data, indent=2, ensure_ascii=False)
    with open(config_path, 'w') as f:
        f.write(output + '\n')
else:
    print(f'    agent_definitions already has: {agents_path}')
PYEOF
    else
        echo -e "  ${YELLOW}[warn]${NC} python3 not available - skipping agent config"
    fi
}

add_skills_source "$USER_CONFIG" "$VIBE_STACK_HOME/core/skills"
add_agent_defs "$USER_CONFIG" "$VIBE_STACK_HOME/core/agents/"

echo -e "  ${GREEN}[OK]${NC} Config updated"
echo ""

# ---- Install CLI Tool ----
echo -e "${BOLD}[3/3] Installing CLI tool...${NC}"

# Determine bin directory (prefer ~/.local/bin, fall back to ~/bin)
if [ -d "$HOME/.local/bin" ] || mkdir -p "$HOME/.local/bin" 2>/dev/null; then
    BIN_DIR="$HOME/.local/bin"
elif [ -d "$HOME/bin" ] || mkdir -p "$HOME/bin" 2>/dev/null; then
    BIN_DIR="$HOME/bin"
else
    echo -e "  ${RED}[✗]${NC} Could not find/create a bin directory in HOME"
    echo "       Manually add bin/vibe-stack to your PATH"
    BIN_DIR=""
fi

if [ -n "$BIN_DIR" ]; then
    CLI_SRC="$VIBE_STACK_HOME/bin/vibe-stack"
    CLI_DEST="$BIN_DIR/vibe-stack"

    if [ ! -f "$CLI_SRC" ]; then
        echo -e "  ${YELLOW}[warn]${NC} CLI script not found at $CLI_SRC"
        echo "       Make sure you have the latest version of opencode-vibe-stack."
    else
        # Make executable
        chmod +x "$CLI_SRC"

        # Create symlink
        if [ -L "$CLI_DEST" ]; then
            rm -f "$CLI_DEST"
        fi
        ln -sf "$CLI_SRC" "$CLI_DEST"
        echo -e "  ${GREEN}[OK]${NC} CLI installed: $CLI_DEST -> $CLI_SRC"

        # Check if BIN_DIR is in PATH
        if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
            echo ""
            echo -e "  ${YELLOW}[!]${NC} ${BOLD}$BIN_DIR${NC} is not in your PATH."
            echo "       Add this to your shell config (~/.bashrc, ~/.zshrc, etc.):"
            echo -e "       ${CYAN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        fi
    fi
fi

echo ""

# ---- Success ----
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✓ Installation Complete!                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Next Steps:${NC}"
echo ""
echo -e "  1. Verify installation:"
echo -e "     ${CYAN}vibe-stack list${NC}"
echo ""
echo -e "  2. Activate domains in a project:"
echo -e "     ${CYAN}cd your-project/${NC}"
echo -e "     ${CYAN}vibe-stack activate game-dev/unity${NC}"
echo ""
echo -e "  3. Check active domains:"
echo -e "     ${CYAN}vibe-stack status${NC}"
echo ""
echo -e "  4. Update the stack later:"
echo -e "     ${CYAN}cd ~/.opencode-vibe-stack && git pull${NC}"
echo -e "     ${CYAN}vibe-stack core-update${NC}"
echo ""
echo -e "  ${BOLD}Location:${NC}    $VIBE_STACK_HOME"
echo -e "  ${BOLD}CLI Tool:${NC}    $BIN_DIR/vibe-stack"
echo ""
