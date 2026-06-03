source "${SCRIPT_DIR}/lib/helpers.sh"
source "${SCRIPT_DIR}/lib/path.sh"
source "${SCRIPT_DIR}/lib/instructions.sh"
source "${SCRIPT_DIR}/lib/mcp.sh"
source "${SCRIPT_DIR}/lib/jsonc.sh"

cmd_core_update() {
    echo -e "${BOLD}Re-syncing core symlinks...${NC}"
    echo ""

    # ---- Part A: Core → User Config per-item link sync ----
    local config_dir="$HOME/.config/opencode"
    local types=("rules" "agents" "commands" "skills" "mcp")

    for type in "${types[@]}"; do
        local src="$VIBE_STACK_HOME/core/$type"
        local dest="$config_dir/$type"

        if [ ! -d "$src" ]; then
            warn "Skipping $type: source not found at $src"
            continue
        fi

        mkdir -p "$config_dir"

        if link_directory_contents "$src" "$dest"; then
            ok "$type/ -> per-item links synced"
        else
            warn "$type/ -> some links may have failed"
        fi
    done

    # Update ~/.config/opencode/opencode.json instructions
    local opencode_json="$config_dir/opencode.json"
    info "Updating core rules in $opencode_json ..."
    sync_opencode_instructions "$opencode_json" "rules/*.md"

    # Register core skills path in user config
    if ! grep -q '"skills"' "$opencode_json" 2>/dev/null; then
        sed -i.bak 's/}[[:space:]]*$/,\n  "skills": {\n    "paths": ["skills"]\n  }\n}/' "$opencode_json" && rm -f "${opencode_json}.bak"
        ok "Registered core skills in skills.paths"
    else
        _jsonc_nested_array_add "$opencode_json" "skills" "paths" '"skills"'
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
                        # Inject "type": "local" if missing (required by OpenCode schema)
                        if (buf !~ /"type"[[:space:]]*:/) {
                            sub(/\{/, "{ \"type\": \"local\", ", buf)
                        }
                        # Escape backslashes in Windows paths for safe gsub replacement
                        if (index(vibe_home, "\\") > 0) gsub(/\\/, "\\\\", vibe_home)
                        gsub(/\$\{VIBE_STACK_HOME\}/, vibe_home, buf)
                        gsub(/[[:space:]]+$/, "", buf)

                        # Strip "release" metadata field (non-MCP config).
                        # Uses brace-counting to correctly remove nested objects
                        # regardless of depth (e.g. repo + asset sub-objects).
                        while (match(buf, /"release"[[:space:]]*:[[:space:]]*\{/)) {
                            rstart = RSTART
                            rpos = RSTART + RLENGTH - 1
                            rlevel = 1
                            while (rlevel > 0 && rpos < length(buf)) {
                                rpos++
                                c = substr(buf, rpos, 1)
                                if (c == "{") rlevel++
                                if (c == "}") rlevel--
                            }
                            before = substr(buf, 1, rstart - 1)
                            after = substr(buf, rpos + 1)
                            sub(/[[:space:]]*,[[:space:]]*$/, "", before)
                            sub(/^[[:space:]]*,[[:space:]]*/, "", after)
                            buf = before after
                        }

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
                        found_mcp = 1; in_mcp = 1; depth = 0
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
                    else if (!in_mcp && found_mcp && found_end) {
                        # MCP was found and rebuilt — close the root object
                        print end_line
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

    # ---- Part B: Domain → Project Config Sync (manifest-driven) ----
    local manifest_file=".opencode/.vibe-stack-active.json"
    if [ -f "$manifest_file" ] && command -v python3 &>/dev/null; then
        info "Syncing domain links..."

        python3 -c "
import json, os, sys

manifest_file = '$manifest_file'
vibe_home = '$VIBE_STACK_HOME'
cwd = os.getcwd()

with open(manifest_file) as f:
    data = json.load(f)
domains = data.get('domains', {})

for domain_key, info in list(domains.items()):
    links = info.get('links', {})
    updated_links = {}
    changes_detected = False

    for dest_rel, src_rel in links.items():
        src_full = os.path.join(vibe_home, src_rel)
        dest_full = os.path.join(cwd, '.opencode', dest_rel)

        if os.path.exists(src_full):
            # Source exists — verify/recreate symlink
            if os.path.islink(dest_full):
                current_target = os.readlink(dest_full)
                if current_target != src_full:
                    # Wrong target — fix it
                    os.unlink(dest_full)
                    os.symlink(src_full, dest_full)
                    changes_detected = True
                    print(f'FIXED: {dest_rel}')
            elif not os.path.exists(dest_full):
                # Missing — create it
                os.makedirs(os.path.dirname(dest_full), exist_ok=True)
                os.symlink(src_full, dest_full)
                changes_detected = True
                print(f'CREATED: {dest_rel}')
            else:
                # Exists but not a symlink — leave it (user file)
                print(f'SKIP (not symlink): {dest_rel}')
            updated_links[dest_rel] = src_rel
        else:
            # Source deleted — this is a stale link
            if os.path.islink(dest_full) or os.path.exists(dest_full):
                os.unlink(dest_full)
                changes_detected = True
                print(f'REMOVED (stale): {dest_rel}')
            # Don't add to updated_links — it's deleted
            changes_detected = True

    # Check for new items in source directories that aren't in manifest
    category = domain_key.split('/')[0]
    domain_name = '/'.join(domain_key.split('/')[1:])
    domain_root = os.path.join(vibe_home, 'domains', category, domain_name)

    for type_dir in ['rules', 'agents', 'commands', 'mcp', 'skills']:
        type_path = os.path.join(domain_root, type_dir)
        if not os.path.isdir(type_path):
            continue

        prefix = f'{category}_{domain_name}'
        for item_name in os.listdir(type_path):
            prefixed_name = f'{prefix}_{item_name}'
            dest_rel = f'{type_dir}/{prefixed_name}'
            src_rel = f'domains/{category}/{domain_name}/{type_dir}/{item_name}'

            if dest_rel not in updated_links:
                # New item — create link
                src_full = os.path.join(vibe_home, src_rel)
                dest_full = os.path.join(cwd, '.opencode', dest_rel)
                os.makedirs(os.path.dirname(dest_full), exist_ok=True)
                os.symlink(src_full, dest_full)
                updated_links[dest_rel] = src_rel
                changes_detected = True
                print(f'NEW: {dest_rel}')

    # Update manifest if changes were made
    if changes_detected:
        info['links'] = updated_links
        with open(manifest_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f'UPDATED: {domain_key}')
" 2>/dev/null || warn "Domain link sync encountered errors"
    fi
}
