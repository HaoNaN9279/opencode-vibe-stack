# ---- JSONC Config Helpers (pure bash, no python required) ----

# Append a value to a JSON array before its closing bracket.
# Usage: _jsonc_array_add <file> <key> <value_line>
# Returns 0 if added, 1 if already present.
_jsonc_array_add() {
    local file="$1" key="$2" val="$3"
    local tmp="${file}.tmp" in_key=false done=false

    [ ! -f "$file" ] && return 1

    while IFS= read -r line || [ -n "$line" ]; do
        if ! $done; then
            if echo "$line" | grep -q "\"$key\""; then
                in_key=true
            fi
            if $in_key && echo "$line" | grep -qE '^[[:space:]]*\][[:space:]]*,?[[:space:]]*$'; then
                echo "$val" >> "$tmp"
                done=true
            fi
        fi
        echo "$line" >> "$tmp"
    done < "$file"

    mv "$tmp" "$file"
    return 0
}
