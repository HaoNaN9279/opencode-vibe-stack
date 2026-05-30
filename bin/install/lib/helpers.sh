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

# ---- Determine VIBE_STACK_HOME ----
# Default to the directory containing this script (the repo root)
VIBE_STACK_HOME="${VIBE_STACK_HOME:-$SCRIPT_DIR}"

# Verify we're in the repo
if [ ! -f "$VIBE_STACK_HOME/core/rules/00-global.md" ] || [ ! -d "$VIBE_STACK_HOME/domains" ]; then
    echo -e "${RED}[✗]${NC} VIBE_STACK_HOME does not appear to be a valid vibe-stack repo: $VIBE_STACK_HOME"
    echo "       Run this script from within the opencode-vibe-stack repository."
    exit 1
fi

echo -e "${GREEN}[✓]${NC} Repo root: ${BOLD}$VIBE_STACK_HOME${NC}"
echo ""
