# ---- Instructions Sync ----

# Sync opencode.json instructions to include core rules
# Usage: sync_opencode_instructions <opencode_json_path> <rules_glob>
sync_opencode_instructions() {
    local config_path="$1"
    local rules_glob="$2"

    if _jsonc_array_has "$config_path" "\"$rules_glob\""; then
        info "instructions already up-to-date"
        return 0
    fi

    if [ ! -f "$config_path" ]; then
        printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "instructions": [\n    "%s"\n  ]\n}\n' "$rules_glob" > "$config_path"
        info "Created $config_path with instructions: $rules_glob"
        return 0
    fi

    if grep -q '"instructions"' "$config_path" 2>/dev/null; then
        _jsonc_array_add "$config_path" "instructions" "    \"$rules_glob\""
    fi
    info "Added instructions: $rules_glob"
}

# Add or remove instructions entry in project-level .opencode/opencode.json
# Usage: modify_project_instructions <config_path> <action:add|remove> <instructions_path>
modify_project_instructions() {
    local config_path="$1"
    local action="$2"
    local instructions_path="$3"

    case "$action" in
        add)
            if _jsonc_array_has "$config_path" "\"$instructions_path\""; then
                return 0
            fi
            if [ ! -f "$config_path" ]; then
                printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "instructions": [\n    "%s"\n  ]\n}\n' "$instructions_path" > "$config_path"
                info "Added instructions: $instructions_path"
                return 0
            fi
            if grep -q '"instructions"' "$config_path" 2>/dev/null; then
                _jsonc_array_add "$config_path" "instructions" "    \"$instructions_path\""
                info "Added instructions: $instructions_path"
            else
                # File exists but has no "instructions" key -- insert one before
                # the closing brace by rewriting the config inline.
                local tmp="${config_path}.tmp"
                awk -v ins="$instructions_path" '
                { lines[NR] = $0 }
                END {
                    for (i = 1; i < NR - 1; i++) print lines[i]
                    # Add trailing comma to the last content line so the
                    # inserted instructions key is valid JSON.
                    sub(/[[:space:]]+$/, "", lines[NR-1])
                    print lines[NR-1] ","
                    print "  \"instructions\": ["
                    print "    \"" ins "\""
                    print "  ]"
                    print lines[NR]
                }
                ' "$config_path" > "$tmp"
                if [ -s "$tmp" ]; then
                    mv "$tmp" "$config_path"
                    _jsonc_fix_trailing_commas "$config_path"
                    info "Added instructions: $instructions_path"
                else
                    rm -f "$tmp"
                    warn "Failed to add instructions to $config_path"
                fi
            fi
            ;;
        remove)
            _jsonc_array_remove "$config_path" "$instructions_path"
            info "Removed instructions: $instructions_path"
            ;;
    esac
}
