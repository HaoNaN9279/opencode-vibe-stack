# ---- Create Core Symlinks ----
echo -e "${BOLD}[1/4] Creating core symlinks...${NC}"

OPENCODE_CONFIG="$HOME/.config/opencode"
mkdir -p "$OPENCODE_CONFIG"

SYMLINK_TYPES=("rules" "agents" "commands" "skills" "mcp")

for type in "${SYMLINK_TYPES[@]}"; do
    src_dir="$VIBE_STACK_HOME/core/$type"
    dest_dir="$OPENCODE_CONFIG/$type"

    if [ ! -d "$src_dir" ]; then
        echo -e "  ${YELLOW}[skip]${NC} $type/ - source not found"
        continue
    fi

    # link_directory_contents handles: old symlink removal, dir creation, per-item linking
    if link_directory_contents "$src_dir" "$dest_dir"; then
        echo -e "  ${GREEN}[OK]${NC} $type/ -> per-item links created"
    else
        echo -e "  ${YELLOW}[warn]${NC} $type/ - some links may have failed"
    fi
done

echo ""
