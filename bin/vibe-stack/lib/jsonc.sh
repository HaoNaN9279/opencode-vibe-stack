# ---- JSONC Array Operations (pure bash, no external deps) ----

# Check if a value string exists in file (literal match)
_jsonc_array_has() {
    local file="$1" val="$2"
    [ -f "$file" ] && grep -qF "$val" "$file" 2>/dev/null
}

# Fix trailing commas before closing JSON brackets
_jsonc_fix_trailing_commas() {
    local file="$1"
    local tmp="${file}.tmp"
    # Use explicit error handling instead of && to avoid orphaned .tmp
    # files when set -e interacts with command list failures.
    awk '
    NR == 1 { prev = $0; next }
    {
        if (prev ~ /,[[:space:]]*$/ && $0 ~ /^[[:space:]]*\]/) {
            sub(/,[[:space:]]*$/, "", prev)
        }
        print prev
        prev = $0
    }
    END { print prev }
    ' "$file" > "$tmp" || { rm -f "$tmp"; return 1; }
    mv "$tmp" "$file"
}

# Add value to JSON array (inserts before closing ])
# Returns: 0=added, 1=key not found, 2=already exists
_jsonc_array_add() {
    local file="$1" key="$2" val="$3"
    local tmp="${file}.tmp" in_key=false done=false

    [ ! -f "$file" ] && return 1

    if _jsonc_array_has "$file" "$val"; then
        return 2
    fi

    if ! grep -q "\"$key\"" "$file" 2>/dev/null; then
        return 1
    fi

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
    _jsonc_fix_trailing_commas "$file"
    return 0
}

# Remove lines containing value from JSON array, fix trailing commas
_jsonc_array_remove() {
    local file="$1" val="$2"
    local tmp="${file}.tmp"

    [ ! -f "$file" ] && return 1

    grep -vF "$val" "$file" > "$tmp"
    mv "$tmp" "$file"
    _jsonc_fix_trailing_commas "$file"
    return 0
}
