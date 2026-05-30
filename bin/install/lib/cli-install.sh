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
