source "${SCRIPT_DIR}/lib/helpers.sh"
source "${SCRIPT_DIR}/lib/path.sh"
source "${SCRIPT_DIR}/lib/mcp.sh"
source "${SCRIPT_DIR}/lib/instructions.sh"
source "${SCRIPT_DIR}/lib/omo-config.sh"

cmd_deactivate() {
    if [ $# -eq 0 ]; then
        die "Usage: vibe-stack deactivate <category/domain> [<category/domain> ...]"
    fi

    for arg in "$@"; do
        local category domain
        category="${arg%%/*}"
        domain="${arg#*/}"

        if [ -z "$category" ] || [ -z "$domain" ] || [ "$category" = "$domain" ]; then
            die "Invalid domain format: '$arg'. Use 'category/domain'."
        fi

        info "Deactivating $category/$domain ..."

        local removed=false
        local subdirs=("rules" "agents" "commands" "mcp" "skills")

        # Determine the domain root to clean up JSONC references
        local domain_root="$VIBE_STACK_HOME/domains/$category/$domain"

        for sub in "${subdirs[@]}"; do
            local dest_link=".opencode/$sub/$domain"
            if [ -L "$dest_link" ]; then
                rm -f "$dest_link"
                removed=true
            elif [ -d "$dest_link" ]; then
                # On Windows, use cmd /c rmdir to safely remove junctions
                # without following into the target directory
                case "$OSTYPE" in
                    msys|cygwin)
                        local win_path
                        win_path="$(posix_to_win "$dest_link")"
                        if cmd /c "rmdir \"$win_path\"" >/dev/null 2>&1; then
                            removed=true
                        else
                            rm -rf "$dest_link" && removed=true
                        fi
                        ;;
                    *)
                        rm -rf "$dest_link" && removed=true
                        ;;
                esac
            fi
        done

        # Clean up empty parent directories
        for sub in "${subdirs[@]}"; do
            local parent=".opencode/$sub"
            if [ -d "$parent" ] && [ -z "$(ls -A "$parent" 2>/dev/null)" ]; then
                rmdir "$parent" 2>/dev/null || true
            fi
        done

        # Remove MCP entries from .opencode/opencode.json
        deactivate_mcp "$domain" "$domain_root"

        # Remove opencode.json instructions for this domain's rules
        if [ -d "$domain_root/rules" ]; then
            modify_project_instructions ".opencode/opencode.json" "remove" "rules/$domain/*.md"
        fi

        # Remove skills path from opencode.json if no skills remain
        if [ ! -d ".opencode/skills" ] || [ -z "$(ls -A ".opencode/skills" 2>/dev/null)" ]; then
            _jsonc_nested_array_remove ".opencode/opencode.json" "skills" "paths" '"skills"'
        fi

        # Clean up oh-my-openagent.jsonc if no active domains remain
        deactivate_omo_config

        if [ "$removed" = true ]; then
            ok "Deactivated $category/$domain"
        else
            warn "No symlinks found for $category/$domain"
        fi
    done
}
