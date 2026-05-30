source "${SCRIPT_DIR}/lib/helpers.sh"
source "${SCRIPT_DIR}/lib/path.sh"
source "${SCRIPT_DIR}/lib/mcp.sh"
source "${SCRIPT_DIR}/lib/instructions.sh"
source "${SCRIPT_DIR}/lib/omo-config.sh"

cmd_activate() {
    if [ $# -eq 0 ]; then
        die "Usage: vibe-stack activate <category/domain> [<category/domain> ...]"
    fi

    local domains_dir="$VIBE_STACK_HOME/domains"
    if [ ! -d "$domains_dir" ]; then
        die "VIBE_STACK_HOME not found: $VIBE_STACK_HOME"
    fi

    # Ensure .opencode/ exists
    mkdir -p .opencode

    for arg in "$@"; do
        local category domain
        category="${arg%%/*}"
        domain="${arg#*/}"

        if [ -z "$category" ] || [ -z "$domain" ] || [ "$category" = "$domain" ]; then
            die "Invalid domain format: '$arg'. Use 'category/domain' (e.g., 'game-dev/unity')."
        fi

        local domain_root="$domains_dir/$category/$domain"
        if [ ! -d "$domain_root" ]; then
            die "Domain not found: $category/$domain\n  Expected at: $domain_root\n  Run 'vibe-stack list' to see available domains."
        fi

        info "Activating $category/$domain ..."

        local activated_types=()
        local subdirs=("rules" "agents" "commands" "mcp" "skills")

        for sub in "${subdirs[@]}"; do
            local src="$domain_root/$sub"
            if [ ! -d "$src" ]; then
                continue
            fi

            local dest_dir=".opencode/$sub"
            mkdir -p "$dest_dir"

            local dest_link="$dest_dir/$domain"

            # Create link (symlink or junction on Windows — never copies)
            if create_dir_link "$src" "$dest_link"; then
                activated_types+=("$sub")
                # Merge MCP configs into .opencode/opencode.json (OpenCode native)
                if [ "$sub" = "mcp" ]; then
                    activate_mcp "$src" "$domain" "$VIBE_STACK_HOME" "$PROJECT_ROOT"
                fi
            else
                warn "Could not link $sub for $domain — skipping"
            fi
        done

        # Update opencode.json instructions for rules (relative to project root)
        if [[ " ${activated_types[*]} " =~ " rules " ]]; then
            modify_project_instructions ".opencode/opencode.json" "add" "rules/$domain/*.md"
        fi

        # Register domain skills path in project opencode.json
        if [[ " ${activated_types[*]} " =~ " skills " ]]; then
            _jsonc_nested_array_add ".opencode/opencode.json" "skills" "paths" '"skills"'
        fi

        # Ensure project-level oh-my-openagent.jsonc exists for skills/agents
        if [[ " ${activated_types[*]} " =~ " skills " ]] || [[ " ${activated_types[*]} " =~ " agents " ]]; then
            activate_omo_config
        fi

        ok "Activated $category/$domain"
        echo "   Types: ${activated_types[*]}"
        echo ""
    done
}
