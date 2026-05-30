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
