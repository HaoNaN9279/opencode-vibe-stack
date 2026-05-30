#!/usr/bin/env bash
# install.sh - OpenCode Vibe Stack One-Click Deploy (Linux / macOS)
# Deploys core symlinks to ~/.config/opencode/ and installs the CLI tool.
# Usage: ./install.sh
# Env: VIBE_STACK_HOME    Override install directory (default: script dir)
# ============================================================================
set -euo pipefail

# Determine repo root and source library modules
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/bin/install/lib"

source "$LIB_DIR/helpers.sh"
source "$LIB_DIR/jsonc.sh"
source "$LIB_DIR/mcp-config.sh"
source "$LIB_DIR/mcp-binaries.sh"
source "$LIB_DIR/symlinks.sh"

# ---- Step 2: Update configuration files ----
echo -e "${BOLD}[2/4] Updating configuration files...${NC}"

OPENCODE_JSON="$OPENCODE_CONFIG/opencode.json"
RULES_GLOB="rules/**/*.md"

if [ ! -f "$OPENCODE_JSON" ]; then
    printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "instructions": [\n    "%s"\n  ]\n}\n' "$RULES_GLOB" > "$OPENCODE_JSON"
    echo -e "  ${GREEN}[OK]${NC} Created $OPENCODE_JSON with instructions: $RULES_GLOB"
elif ! grep -qF "\"$RULES_GLOB\"" "$OPENCODE_JSON"; then
    if _jsonc_array_add "$OPENCODE_JSON" "instructions" "    \"$RULES_GLOB\""; then
        echo -e "  ${GREEN}[OK]${NC} Added instructions: $RULES_GLOB"
    else
        echo -e "  ${YELLOW}[!]${NC} Could not auto-update $OPENCODE_JSON — please add \"$RULES_GLOB\" to the instructions array manually"
    fi
else
    echo -e "  ${GREEN}[OK]${NC} instructions already has: $RULES_GLOB"
fi
echo ""

# Merge core/mcp configurations
merge_core_mcp_configs "$VIBE_STACK_HOME" "$OPENCODE_JSON"
echo ""

# ---- Step 3: Install MCP binaries ----
echo -e "${BOLD}[3/4] Installing MCP binaries...${NC}"
install_mcp_binaries "$VIBE_STACK_HOME"

# ---- Step 4: Install CLI tool ----
source "$LIB_DIR/cli-install.sh"

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
echo -e "     ${CYAN}cd $VIBE_STACK_HOME && git pull${NC}"
echo -e "     ${CYAN}vibe-stack core-update${NC}"
echo ""
echo -e "  ${BOLD}Location:${NC}    $VIBE_STACK_HOME"
echo -e "  ${BOLD}CLI Tool:${NC}    $BIN_DIR/vibe-stack"
echo ""
