# ---- Merge Core/MCP Configs ----
# Merges core/mcp/*.json server entries into opencode.json
# under the "mcp" key with "vibe:core-" prefixed server names.
merge_core_mcp_configs() {
    local vibe_home="$1"
    local opencode_json="$2"
    local mcp_dir="$vibe_home/core/mcp"

    [ ! -d "$mcp_dir" ] && return 0

    # Collect JSON files from core/mcp
    local json_files
    json_files=$(ls "$mcp_dir"/*.json 2>/dev/null || true)
    [ -z "$json_files" ] && return 0

    # Ensure opencode.json has an "mcp" object
    if ! grep -q '"mcp"' "$opencode_json" 2>/dev/null; then
        sed -i.bak 's/}$/,\n  "mcp": {}\n}/' "$opencode_json" && rm -f "${opencode_json}.bak"
    fi

    local count=0
    for f in $json_files; do
        local name
        name=$(basename "$f" .json)
        local key="vibe:core-${name}"

        # Skip if this server is already configured
        grep -q "\"${key}\"" "$opencode_json" 2>/dev/null && continue

        # Extract the server entry from core/mcp/*.json and rename the key
        local entry
        entry=$(awk -v k="$key" '
            /"mcp"/ { capture=1; next }
            capture && !server_line {
                gsub(/"[^"]*"[[:space:]]*:/, "\"" k "\": ")
                print
                server_line=1
                brace += gsub(/\{/, "&")
                brace -= gsub(/\}/, "&")
                if (brace <= 0) { exit }
                next
            }
            capture && server_line {
                print
                brace += gsub(/\{/, "&")
                brace -= gsub(/\}/, "&")
                if (brace <= 0) { exit }
            }
        ' "$f")

        [ -z "$entry" ] && continue

        # Write entry to a temp file for safe awk processing
        local tmp_entry
        tmp_entry=$(mktemp 2>/dev/null || echo "${opencode_json}.entry.$$")
        printf '%s\n' "$entry" > "$tmp_entry"

        # Insert entry into the "mcp" object in opencode.json
        awk -v tmp="$tmp_entry" '
            /"mcp"/ { in_mcp=1 }
            in_mcp && /^[[:space:]]*\}[[:space:]]*,?[[:space:]]*$/ {
                while ((getline line < tmp) > 0) {
                    print line
                }
                close(tmp)
                print ","
                in_mcp=0
            }
            { print }
        ' "$opencode_json" > "${opencode_json}.tmp" && mv "${opencode_json}.tmp" "$opencode_json"

        rm -f "$tmp_entry"
        count=$((count + 1))
    done

    if [ "$count" -gt 0 ]; then
        echo -e "  ${GREEN}[OK]${NC} MCP activated ($count servers with vibe:core- prefix)"
    fi
}
