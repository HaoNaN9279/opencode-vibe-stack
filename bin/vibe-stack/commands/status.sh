source "${SCRIPT_DIR}/lib/helpers.sh"

cmd_status() {
    echo -e "${BOLD}Active Domains in $PROJECT_ROOT:${NC}"
    echo ""

    if [ ! -d ".opencode" ]; then
        echo "  No .opencode/ directory found. No domains active."
        return
    fi

    # ---- Manifest-based detection (primary) ----
    if [ -f ".opencode/.vibe-stack-active.json" ] && command -v python3 &>/dev/null; then
        python3 <<'PYEOF' 2>/dev/null && return
import json, sys
GREEN = '\033[0;32m'
NC = '\033[0m'
BULLET = '\u25cf'
try:
    with open('.opencode/.vibe-stack-active.json') as f:
        data = json.load(f)
except (json.JSONDecodeError, IOError):
    sys.exit(1)
domains = data.get('domains', {})
if not domains:
    print("  No domains active. Use 'vibe-stack activate <category/domain>' to add one.")
else:
    for domain_key in sorted(domains.keys()):
        info = domains[domain_key]
        links = info.get('links', {})
        type_counts = {}
        for link_path in links:
            type_name = link_path.split('/')[0]
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        print(f'  {GREEN}{BULLET}{NC} {domain_key}')
        for t in sorted(type_counts.keys()):
            c = type_counts[t]
            print(f'    {t}/: {c} links')
PYEOF
        # python3 failed (bad JSON, etc.) → fall through to fallback
    fi

    # ---- Fallback: scan directories (legacy installs without manifest) ----
    local found=false

    for type_dir in rules agents commands mcp skills; do
        local odir=".opencode/$type_dir"
        if [ ! -d "$odir" ]; then
            continue
        fi

        shopt -s nullglob
        for link in "$odir"/*; do
            [ -e "$link" ] || continue
            local item
            item="$(basename "$link")"
            local target
            if [ -L "$link" ]; then
                target="$(readlink "$link")"
            else
                target="$link  (copy, no symlink support)"
            fi

            if [ "$found" = false ]; then
                found=true
            fi

            echo -e "  ${GREEN}●${NC} $item  ($type_dir)"
            echo -e "    -> $target"
        done
        shopt -u nullglob
    done

    if [ "$found" = false ]; then
        echo "  No domains active. Use 'vibe-stack activate <category/domain>' to add one."
    fi

    echo ""
}
