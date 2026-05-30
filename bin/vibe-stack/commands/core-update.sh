source "${SCRIPT_DIR}/lib/helpers.sh"
source "${SCRIPT_DIR}/lib/path.sh"
source "${SCRIPT_DIR}/lib/instructions.sh"
source "${SCRIPT_DIR}/lib/mcp.sh"

cmd_core_update() {
    echo -e "${BOLD}Re-syncing core symlinks...${NC}"
    echo ""

    local config_dir="$HOME/.config/opencode"
    local types=("rules" "agents" "commands" "skills" "mcp")
    local updated=false

    for type in "${types[@]}"; do
        local src="$VIBE_STACK_HOME/core/$type"
        local dest="$config_dir/$type"

        if [ ! -d "$src" ]; then
            warn "Skipping $type: source not found at $src"
            continue
        fi

        mkdir -p "$config_dir"

        if [ -L "$dest" ]; then
            local current
            current="$(readlink "$dest")"
            if [ "$current" = "$src" ]; then
                ok "$type/ -> already up-to-date"
                continue
            fi
        elif [ -d "$dest" ]; then
            # Might be a junction on Windows (not detected by -L)
            ok "$type/ -> already linked"
            continue
        fi

        # Remove existing and re-link (create_dir_link handles junctions safely)
        if ! create_dir_link "$src" "$dest"; then
            warn "Failed to link $type/"
            continue
        fi
        ok "$type/ -> linked"
        updated=true
    done

    # Update ~/.config/opencode/opencode.json instructions
    # Path is relative to the config directory (where rules/ symlink lives)
    local opencode_json="$config_dir/opencode.json"
    info "Updating core rules in $opencode_json ..."
    sync_opencode_instructions "$opencode_json" "rules/*.md"

    if [ "$updated" = true ]; then
        ok "Core symlinks updated."
    fi

    # Re-download MCP binaries (idempotent – skips already-installed)
    echo ""
    info "Checking for new or updated MCP binaries..."
    install_mcp_binaries "$VIBE_STACK_HOME"
}
