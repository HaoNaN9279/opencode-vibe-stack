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
echo -e "${BOLD}[1/4] Creating core symlinks...${NC}"

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

# ---- Update configuration files ----
echo -e "${BOLD}[2/4] Updating configuration files...${NC}"

OPENCODE_JSON="$OPENCODE_CONFIG/opencode.json"
RULES_GLOB="rules/*.md"
USER_CONFIG="$OPENCODE_CONFIG/oh-my-openagent.jsonc"
CONFIG_MANAGER="$VIBE_STACK_HOME/script/config_manager.py"

if command -v python3 &>/dev/null; then
    # 2a. Update opencode.json with core rules as instructions
    python3 "$CONFIG_MANAGER" add-instructions "$OPENCODE_JSON" "$RULES_GLOB"
    echo ""

    # 2b. Update oh-my-openagent.jsonc
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

    python3 "$CONFIG_MANAGER" add-skills-source "$USER_CONFIG" "$VIBE_STACK_HOME/core/skills"
    python3 "$CONFIG_MANAGER" add-agent-defs "$USER_CONFIG" "$VIBE_STACK_HOME/core/agents/"

    echo -e "  ${GREEN}[OK]${NC} Config updated"
else
    echo -e "  ${YELLOW}[warn]${NC} python3 not available - skipping config updates"
fi

echo ""

# ---- Bootstrap MCP Dependencies ----
bootstrap_mcp_deps() {
    local vibe_home="$1"

    # Init submodules
    if [ -f "$vibe_home/.gitmodules" ]; then
        echo -e "  ${CYAN}[i]${NC} Initializing git submodules..."
        if git -C "$vibe_home" submodule update --init --recursive 2>/dev/null; then
            echo -e "  ${GREEN}[OK]${NC} Submodules ready"
        else
            echo -e "  ${YELLOW}[warn]${NC} Submodule init failed — some MCPs may not work"
            echo "       Run: cd $vibe_home && git submodule update --init --recursive"
        fi
    fi

    local has_uv=false;  command -v uv  &>/dev/null && has_uv=true
    local has_pip=false; command -v pip &>/dev/null && has_pip=true
    local has_npm=false; command -v npm &>/dev/null && has_npm=true

    local found_any=false

    # Python projects under domains/*/mcp/
    while IFS= read -r -d '' pyproject; do
        local dir
        dir=$(dirname "$pyproject")
        local label
        label=$(echo "$dir" | sed "s|$vibe_home/||")
        echo -e "  ${CYAN}[i]${NC} $label ..."
        if $has_uv; then
            (cd "$dir" && uv sync 2>/dev/null) && \
                echo -e "    ${GREEN}[OK]${NC} uv sync" || \
                echo -e "    ${YELLOW}[warn]${NC} uv sync failed"
        elif $has_pip; then
            (cd "$dir" && pip install -e "." --quiet 2>/dev/null) && \
                echo -e "    ${GREEN}[OK]${NC} pip install" || \
                echo -e "    ${YELLOW}[warn]${NC} pip install failed"
        else
            echo -e "    ${YELLOW}[warn]${NC} Neither uv nor pip found — install manually"
        fi
        found_any=true
    done < <(find "$vibe_home/domains" -name "pyproject.toml" -path "*/mcp/*" -not -path "*/.git/*" -print0 2>/dev/null)

    # Node.js projects under domains/*/mcp/
    while IFS= read -r -d '' pkgjson; do
        local dir
        dir=$(dirname "$pkgjson")
        # Skip if already installed
        if [ -d "$dir/node_modules" ]; then continue; fi
        local label
        label=$(echo "$dir" | sed "s|$vibe_home/||")
        echo -e "  ${CYAN}[i]${NC} $label ..."
        if $has_npm; then
            (cd "$dir" && npm install --silent 2>/dev/null) && \
                echo -e "    ${GREEN}[OK]${NC} npm install" || \
                echo -e "    ${YELLOW}[warn]${NC} npm install failed"
        else
            echo -e "    ${YELLOW}[warn]${NC} npm not found — install manually"
        fi
        found_any=true
    done < <(find "$vibe_home/domains" -name "package.json" -path "*/mcp/*" -not -path "*/node_modules/*" -not -path "*/.git/*" -print0 2>/dev/null)

    if [ "$found_any" = false ]; then
        echo -e "  ${CYAN}[i]${NC} No MCP code directories found — nothing to bootstrap"
    fi
}

echo -e "${BOLD}[3/4] Bootstrapping MCP dependencies...${NC}"
echo ""
bootstrap_mcp_deps "$VIBE_STACK_HOME"
echo ""

# ---- Install CLI Tool ----
echo -e "${BOLD}[4/4] Installing CLI tool...${NC}"

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
