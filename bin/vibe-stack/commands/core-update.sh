source "${SCRIPT_DIR}/lib/helpers.sh"
source "${SCRIPT_DIR}/lib/path.sh"
source "${SCRIPT_DIR}/lib/instructions.sh"
source "${SCRIPT_DIR}/lib/mcp.sh"
source "${SCRIPT_DIR}/lib/jsonc.sh"

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
    sync_opencode_instructions "$opencode_json" "rules/**/*.md"

    # Register core skills path in user config
    if ! grep -q '"skills"' "$opencode_json" 2>/dev/null; then
        sed -i.bak 's/}[[:space:]]*$/,\n  "skills": {\n    "paths": ["skills"]\n  }\n}/' "$opencode_json" && rm -f "${opencode_json}.bak"
        ok "Registered core skills in skills.paths"
    else
        _jsonc_nested_array_add "$opencode_json" "skills" "paths" '"skills"'
    fi

    if [ "$updated" = true ]; then
        ok "Core symlinks updated."
    fi

    # Re-download MCP binaries (idempotent – skips already-installed)
    echo ""
    info "Checking for new or updated MCP binaries..."
    install_mcp_binaries "$VIBE_STACK_HOME"

    # ---- Merge core/mcp MCP configs into user config ----
    local mcp_dir="$VIBE_STACK_HOME/core/mcp"
    if [ -d "$mcp_dir" ]; then
        local json_files
        json_files=$(ls "$mcp_dir"/*.json 2>/dev/null || true)
        if [ -n "$json_files" ]; then
            info "Merging core MCP configs..."
            local user_config="$config_dir/opencode.json"
            touch "$user_config" 2>/dev/null || true

            # Extract MCP server entries from core/mcp/*.json, prefix with vibe:core-
            local mcp_tmp
            mcp_tmp=$(mktemp)

            for f in $json_files; do
                awk -v vibe_home="$VIBE_STACK_HOME" '
                BEGIN { in_mcp=0; server=""; depth=0; buf="" }
                { gsub(/\/\/.*$/, ""); gsub(/^[[:space:]]+/, "") }
                /^"mcp"/ || /^"mcpServers"/ { in_mcp=1; next }
                in_mcp && server == "" && /^"[^"]+"[[:space:]]*:[[:space:]]*\{/ {
                    server = $0
                    gsub(/[[:space:]]*:.*/, "", server)
                    gsub(/"/, "", server)
                    sub(/^"[^"]+"[[:space:]]*:[[:space:]]*/, "", $0)
                    depth = 0; buf = ""
                }
                in_mcp && server != "" {
                    buf = buf $0 " "
                    n = split($0, chs, "")
                    for (i = 1; i <= n; i++) {
                        if (chs[i] == "{") depth++
                        if (chs[i] == "}") { depth--; if (depth == 0) break }
                    }
                    if (depth == 0) {
                        gsub(/\$\{VIBE_STACK_HOME\}/, vibe_home, buf)
                        gsub(/[[:space:]]+$/, "", buf)
                        printf "vibe:core-%s\t%s\n", server, buf
                        server = ""; buf = ""
                    }
                }
                ' "$f" >> "$mcp_tmp"
            done

            if [ -s "$mcp_tmp" ]; then
                # Merge collected MCP entries into user config mcp block
                awk -v mcp_file="$mcp_tmp" '
                BEGIN {
                    while ((getline < mcp_file) > 0) {
                        tab = index($0, "\t")
                        if (tab > 0) {
                            name = substr($0, 1, tab-1)
                            cfg  = substr($0, tab+1)
                            new_names[++n_new] = name
                            new_configs[name] = cfg
                        }
                    }
                    close(mcp_file)
                }
                !in_mcp {
                    if ($0 ~ /^[[:space:]]*"mcp"/) {
                        in_mcp = 1; depth = 0
                        if ($0 ~ /\{/) depth++
                        next
                    }
                    else if ($0 ~ /^[[:space:]]*\}/ && !found_end && !in_mcp) {
                        found_end = 1; end_line = $0
                        next
                    }
                    else { print }
                    next
                }
                {
                    opens = gsub(/{/, "{", $0)
                    closes = gsub(/}/, "}", $0)
                    depth += opens - closes
                    if (depth <= 0) {
                        print "  \"mcp\": {"
                        for (i = 1; i <= n_new; i++) {
                            comma = (i < n_new) ? "," : ""
                            print "    \"" new_names[i] "\": " new_configs[new_names[i]] comma
                        }
                        comma_suffix = ($0 ~ /,$/ ? "," : "")
                        print "  }" comma_suffix
                        in_mcp = 0; depth = 0
                        next
                    }
                }
                END {
                    if (!in_mcp && !found_mcp && found_end) {
                        print "  \"mcp\": {"
                        for (i = 1; i <= n_new; i++) {
                            comma = (i < n_new) ? "," : ""
                            print "    \"" new_names[i] "\": " new_configs[new_names[i]] comma
                        }
                        print "  }"
                        print end_line
                    }
                    else if (!in_mcp && !found_mcp && !found_end) {
                        print "{"
                        print "  \"$schema\": \"https://opencode.ai/config.json\","
                        print "  \"mcp\": {"
                        for (i = 1; i <= n_new; i++) {
                            comma = (i < n_new) ? "," : ""
                            print "    \"" new_names[i] "\": " new_configs[new_names[i]] comma
                        }
                        print "  }"
                        print "}"
                    }
                }
                ' "$user_config" > "${user_config}.tmp" 2>/dev/null

                if [ -s "${user_config}.tmp" ]; then
                    _jsonc_fix_trailing_commas "${user_config}.tmp"
                    mv "${user_config}.tmp" "$user_config"
                    ok "Core MCP configs merged"
                    while IFS= read -r line; do
                        local srv_name="${line%%$'\t'*}"
                        [ -n "$srv_name" ] && info "    + $srv_name"
                    done < "$mcp_tmp"
                else
                    warn "Core MCP merge: failed to process $user_config"
                    rm -f "${user_config}.tmp"
                fi
            fi

            rm -f "$mcp_tmp"
        fi
    fi
}
