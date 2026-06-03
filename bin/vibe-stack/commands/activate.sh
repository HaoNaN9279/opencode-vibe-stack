source "${SCRIPT_DIR}/lib/helpers.sh"
source "${SCRIPT_DIR}/lib/path.sh"
source "${SCRIPT_DIR}/lib/mcp.sh"
source "${SCRIPT_DIR}/lib/instructions.sh"
source "${SCRIPT_DIR}/lib/omo-config.sh"

# ------------------------------------------------------------------
# _manifest_has_domain — check if domain key exists in manifest
# Returns: 0 (found), 1 (not found or manifest missing)
# ------------------------------------------------------------------
_manifest_has_domain() {
    local manifest="$1"
    local domain_key="$2"
    [ ! -f "$manifest" ] && return 1

    if command -v python3 &>/dev/null; then
        python3 -c "
import json
with open('$manifest') as f:
    data = json.load(f)
if '$domain_key' in data.get('domains', {}):
    exit(0)
else:
    exit(1)
" 2>/dev/null && return 0
        return 1
    fi

    grep -q "\"$domain_key\"" "$manifest" 2>/dev/null
}

# ------------------------------------------------------------------
# _manifest_write_domain — write domain links entry into manifest
# Args: manifest_file domain_key link_entry...
#   link_entry format: "dest_rel|src_rel" (e.g. "rules/blender-01.md|domains/dcc/blender/rules/01.md")
# Returns: 0 on success, 1 on failure
# ------------------------------------------------------------------
_manifest_write_domain() {
    local manifest_file="$1"
    local domain_key="$2"
    shift 2

    if ! command -v python3 &>/dev/null; then
        warn "python3 not available — manifest creation skipped"
        return 1
    fi

    python3 -c "
import json, sys
domain_key = '$domain_key'
with open('$manifest_file') as f:
    data = json.load(f)
domains = data.setdefault('domains', {})
links = {}
for arg in sys.argv[1:]:
    dest, src = arg.split('|', 1)
    links[dest] = src
domains[domain_key] = {'links': links}
with open('$manifest_file', 'w') as f:
    json.dump(data, f, indent=2)
" "$@" 2>/dev/null || {
        warn "Failed to write manifest for $domain_key"
        return 1
    }
}

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

    # Initialize manifest if not exists
    local manifest_file=".opencode/.vibe-stack-active.json"
    if [ ! -f "$manifest_file" ]; then
        echo '{"version":1,"domains":{}}' > "$manifest_file"
    fi

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

        # Reject duplicate activation
        if _manifest_has_domain "$manifest_file" "$category/$domain"; then
            die "Domain $category/$domain is already activated"
        fi

        info "Activating $category/$domain ..."

        local activated_types=()
        local manifest_args=()
        local subdirs=("rules" "agents" "commands" "mcp" "skills")

        for sub in "${subdirs[@]}"; do
            local src="$domain_root/$sub"
            if [ ! -d "$src" ]; then
                continue
            fi

            local dest_dir=".opencode/$sub"
            mkdir -p "$dest_dir"

            # Create per-item links (symlink or junction on Windows — never copies)
            if link_directory_contents "$src" "$dest_dir" "${category}_${domain}"; then
                activated_types+=("$sub")

                # Collect link entries for manifest AFTER successful linking
                shopt -s nullglob
                for item in "$src"/*; do
                    local item_name="$(basename "$item")"
                    local prefixed="${category}_${domain}_${item_name}"
                    manifest_args+=("${sub}/${prefixed}|domains/${category}/${domain}/${sub}/${item_name}")
                done
                shopt -u nullglob

                # Merge MCP configs into .opencode/opencode.json (OpenCode native)
                if [ "$sub" = "mcp" ]; then
                    activate_mcp "$src" "$domain" "$VIBE_STACK_HOME" "$PROJECT_ROOT"
                fi
            else
                warn "Could not link $sub for $domain — skipping"
            fi
        done

        # Write manifest entry
        if [ ${#manifest_args[@]} -gt 0 ]; then
            _manifest_write_domain "$manifest_file" "$category/$domain" "${manifest_args[@]}"
        fi

        # Update opencode.json instructions for rules (relative to project root)
        if [[ " ${activated_types[*]} " =~ " rules " ]]; then
            modify_project_instructions ".opencode/opencode.json" "add" "rules/*.md"
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

    # Auto-download MCP binaries for all newly activated domains
    install_mcp_binaries "$VIBE_STACK_HOME"
}
