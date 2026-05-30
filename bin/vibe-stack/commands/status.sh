source "${SCRIPT_DIR}/lib/helpers.sh"

cmd_status() {
    echo -e "${BOLD}Active Domains in $PROJECT_ROOT:${NC}"
    echo ""

    if [ ! -d ".opencode" ]; then
        echo "  No .opencode/ directory found. No domains active."
        return
    fi

    local found=false

    for type_dir in rules agents commands mcp skills; do
        local odir=".opencode/$type_dir"
        if [ ! -d "$odir" ]; then
            continue
        fi

        # Use -d (follows symlinks) instead of -L to support Windows
        # where ln -s may fall back to copying directories without symlinks
        shopt -s nullglob
        for link in "$odir"/*; do
            [ -d "$link" ] || continue
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
