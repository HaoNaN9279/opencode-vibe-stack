source "${SCRIPT_DIR}/lib/helpers.sh"

# ---- Manifest Helpers ----

# Read active domain keys from manifest as "category/domain" per line
# Returns 0 on success, 1 if no manifest or python3 unavailable
_manifest_read_active() {
    local manifest=".opencode/.vibe-stack-active.json"
    [ ! -f "$manifest" ] && return 1

    if command -v python3 &>/dev/null; then
        python3 -c "
import json, sys
try:
    with open('$manifest') as f:
        data = json.load(f)
    for key in data.get('domains', {}):
        print(key)
except Exception:
    sys.exit(1)
" 2>/dev/null
        return 0
    fi
    return 1
}

# ---- Domain Scanning ----

# List all domains as "category/domain"
list_all_domains() {
    local domains_dir="$VIBE_STACK_HOME/domains"
    if [ ! -d "$domains_dir" ]; then
        die "VIBE_STACK_HOME not found. Run 'install.sh' first.\n  Expected: $VIBE_STACK_HOME"
    fi

    for cat_dir in "$domains_dir"/*/; do
        [ -d "$cat_dir" ] || continue
        local category
        category="$(basename "$cat_dir")"
        for domain_dir in "$cat_dir"*/; do
            [ -d "$domain_dir" ] || continue
            local domain
            domain="$(basename "$domain_dir")"
            # Check if this domain has any actual config dirs
            local has_configs=false
            for sub in rules agents commands mcp skills tools; do
                if [ -d "$domain_dir/$sub" ]; then
                    has_configs=true
                    break
                fi
            done
            if [ "$has_configs" = true ]; then
                echo "$category/$domain"
            fi
        done
    done
}

# ---- Commands ----

cmd_list() {
    echo -e "${BOLD}Available Domains:${NC}"
    echo ""

    local domains_dir="$VIBE_STACK_HOME/domains"
    if [ ! -d "$domains_dir" ]; then
        die "VIBE_STACK_HOME not found: $VIBE_STACK_HOME\nRun install.sh first."
    fi

    # Build set of active domains from manifest (if available)
    local active_domains
    active_domains="$(_manifest_read_active)" || true

    local current_cat=""
    while IFS= read -r full_domain; do
        local category="${full_domain%%/*}"
        local domain="${full_domain#*/}"

        if [ "$category" != "$current_cat" ]; then
            if [ -n "$current_cat" ]; then echo ""; fi
            echo -e "  ${BOLD}[$category]${NC}"
            current_cat="$category"
        fi

        # Check if active in current project
        local active_mark="  "
        if [ -n "$active_domains" ]; then
            # Manifest-based detection
            if echo "$active_domains" | grep -q -F -x "$category/$domain"; then
                active_mark=" *"
            fi
        else
            # Fallback: old-style directory check (pre-flat-link)
            # Use -d (not -L) to support Windows where ln -s may copy dirs
            if [ -d ".opencode/rules/$domain" ]; then
                active_mark=" *"
            fi
        fi

        echo -e "  $active_mark $domain"
    done < <(list_all_domains)

    echo ""
    echo -e "  ${CYAN}*${NC} = active in current project"
    echo ""
    echo "Use 'vibe-stack status' for details on active domains."
}
