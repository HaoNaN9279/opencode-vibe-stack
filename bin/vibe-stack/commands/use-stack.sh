source "${SCRIPT_DIR}/lib/helpers.sh"

cmd_use_stack() {
    local stack_name="${1:-}"

    if [ -z "$stack_name" ]; then
        echo "Usage: vibe-stack use-stack <stack-name>"
        echo ""
        echo "Available stacks:"
        if [ -d "$VIBE_STACK_HOME/stacks" ] && [ -n "$(ls -A "$VIBE_STACK_HOME/stacks" 2>/dev/null)" ]; then
            for stack_file in "$VIBE_STACK_HOME/stacks"/*.json; do
                [ -f "$stack_file" ] || continue
                local name
                name="$(basename "$stack_file" .json)"
                echo "  $name"
            done
        else
            echo "  (none - stacks/ directory is empty)"
            echo ""
            echo "  To create a stack, add a JSON file like:"
            echo "    $VIBE_STACK_HOME/stacks/game-dev.json"
            echo '    { "domains": ["game-dev/unity", "game-dev/unreal"] }'
        fi
        return 1
    fi

    local stack_file="$VIBE_STACK_HOME/stacks/$stack_name.json"
    if [ ! -f "$stack_file" ]; then
        die "Stack not found: $stack_name\n  Expected: $stack_file\n  Use 'vibe-stack use-stack' to list available stacks."
    fi

    info "Loading stack: $stack_name"

    # Read domains from JSON stack file via grep
    domains=$(grep -oE '"[a-z0-9_-]+/[a-z0-9_-]+"' "$stack_file" | tr -d '"' || true)

    if [ -z "$domains" ]; then
        die "No domains found in stack '$stack_name'. Expected 'domains' array in JSON."
    fi

    echo ""
    while IFS= read -r domain; do
        [ -z "$domain" ] && continue
        cmd_activate "$domain"
    done <<< "$domains"

    ok "Stack '$stack_name' activated."
}
