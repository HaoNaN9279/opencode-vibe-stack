source "${SCRIPT_DIR}/lib/helpers.sh"
source "${SCRIPT_DIR}/lib/path.sh"
source "${SCRIPT_DIR}/lib/mcp.sh"
source "${SCRIPT_DIR}/lib/instructions.sh"
source "${SCRIPT_DIR}/lib/omo-config.sh"

# ------------------------------------------------------------------
# _manifest_remove_domain — remove a domain entry from the manifest
# Returns: 0 on success, 1 if manifest missing or python3 unavailable
# Prints: REMOVED | DELETED | NOT_FOUND (to stdout)
# ------------------------------------------------------------------
_manifest_remove_domain() {
    local domain_key="$1"
    local manifest=".opencode/.vibe-stack-active.json"
    [ ! -f "$manifest" ] && return 1

    if command -v python3 &>/dev/null; then
        python3 -c "
import json
with open('$manifest') as f:
    data = json.load(f)
domains = data.get('domains', {})
if '$domain_key' in domains:
    del domains['$domain_key']
    if domains:
        with open('$manifest', 'w') as f:
            json.dump(data, f, indent=2)
        print('REMOVED')
    else:
        import os
        os.remove('$manifest')
        print('DELETED')
else:
    print('NOT_FOUND')
" 2>/dev/null
        return $?
    fi

    return 1
}

# ------------------------------------------------------------------
# _manifest_get_links — retrieve link entries for a domain from manifest
# Prints one line per link:  dest_relative|source_relative
# Returns 0 on success (even if no links), 1 if manifest missing
# ------------------------------------------------------------------
_manifest_get_links() {
    local domain_key="$1"
    local manifest=".opencode/.vibe-stack-active.json"
    [ ! -f "$manifest" ] && return 1

    if command -v python3 &>/dev/null; then
        python3 -c "
import json, sys
with open('$manifest') as f:
    data = json.load(f)
links = data.get('domains', {}).get('$domain_key', {}).get('links', {})
if links:
    for dest, src in links.items():
        print(f'{dest}|{src}')
" 2>/dev/null
        return 0
    fi

    return 1
}

cmd_deactivate() {
    if [ $# -eq 0 ]; then
        die "Usage: vibe-stack deactivate <category/domain> [<category/domain> ...]"
    fi

    for arg in "$@"; do
        local category domain domain_key domain_root
        category="${arg%%/*}"
        domain="${arg#*/}"

        if [ -z "$category" ] || [ -z "$domain" ] || [ "$category" = "$domain" ]; then
            die "Invalid domain format: '$arg'. Use 'category/domain'."
        fi

        info "Deactivating $category/$domain ..."

        domain_key="$category/$domain"
        domain_root="$VIBE_STACK_HOME/domains/$category/$domain"
        local removed=false
        local subdirs=("rules" "agents" "commands" "mcp" "skills")

        # === Manifest-driven link removal ===
        local manifest=".opencode/.vibe-stack-active.json"
        if [ -f "$manifest" ]; then
            local links_output
            links_output="$(_manifest_get_links "$domain_key")"
            if [ -n "$links_output" ]; then
                while IFS='|' read -r link_dest link_src; do
                    [ -n "$link_dest" ] && rm -f "$link_dest"
                    removed=true
                done <<< "$links_output"

                # Clean up empty parent directories
                for sub in "${subdirs[@]}"; do
                    local parent=".opencode/$sub"
                    if [ -d "$parent" ] && [ -z "$(ls -A "$parent" 2>/dev/null)" ]; then
                        rmdir "$parent" 2>/dev/null || true
                    fi
                done

                # Remove domain entry from manifest
                _manifest_remove_domain "$domain_key" >/dev/null 2>&1 || true
            fi
        fi

        # === Fallback: old scanning logic (no manifest or domain not found) ===
        if [ "$removed" = false ]; then
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
        fi

        # === Common cleanup (runs regardless of approach) ===
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
