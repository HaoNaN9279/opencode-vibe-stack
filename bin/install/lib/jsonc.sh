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

# Add value to a nested JSON array (inserts before closing ])
# Usage: _jsonc_nested_array_add <file> <parent_key> <child_key> <value>
# Returns: 0=added, 1=parent key not found, 2=value already exists
_jsonc_nested_array_add() {
    local file="$1" parent_key="$2" child_key="$3" val="$4"
    local tmp="${file}.tmp" found_parent=false found_child=false done=false

    [ ! -f "$file" ] && return 1

    # Check if value already exists (inline _jsonc_array_has)
    if grep -qF "$val" "$file" 2>/dev/null; then
        return 2
    fi

    # Check if parent key exists
    if ! grep -q "\"$parent_key\"" "$file" 2>/dev/null; then
        return 1
    fi

    while IFS= read -r line || [ -n "$line" ]; do
        if ! $done; then
            if ! $found_parent; then
                if echo "$line" | grep -q "\"$parent_key\""; then
                    found_parent=true
                fi
            elif ! $found_child; then
                if echo "$line" | grep -q "\"$child_key\""; then
                    found_child=true
                fi
            else
                if echo "$line" | grep -qE '^[[:space:]]*\][[:space:]]*,?[[:space:]]*$'; then
                    echo "$val" >> "$tmp"
                    done=true
                fi
            fi
        fi
        echo "$line" >> "$tmp"
    done < "$file"

    mv "$tmp" "$file"

    # Fix trailing commas (inline _jsonc_fix_trailing_commas)
    local tmp2="${file}.tmp2"
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
    ' "$file" > "$tmp2" || { rm -f "$tmp2"; return 1; }
    mv "$tmp2" "$file"
    return 0
}

# Remove value line from a nested JSON array, fix trailing commas
# Usage: _jsonc_nested_array_remove <file> <parent_key> <child_key> <value>
# Returns: 0=removed
_jsonc_nested_array_remove() {
    local file="$1" parent_key="$2" child_key="$3" val="$4"
    local tmp="${file}.tmp"
    local found_parent=false found_child=false in_array=false

    [ ! -f "$file" ] && return 1

    while IFS= read -r line || [ -n "$line" ]; do
        if ! $found_parent; then
            if echo "$line" | grep -q "\"$parent_key\""; then
                found_parent=true
            fi
            echo "$line" >> "$tmp"
        elif ! $found_child; then
            if echo "$line" | grep -q "\"$child_key\""; then
                found_child=true
                in_array=true
            fi
            echo "$line" >> "$tmp"
        elif $in_array; then
            if echo "$line" | grep -qE '^[[:space:]]*\][[:space:]]*,?[[:space:]]*$'; then
                in_array=false
                echo "$line" >> "$tmp"
            elif echo "$line" | grep -qF "$val"; then
                # Skip this line (remove the value)
                :
            else
                echo "$line" >> "$tmp"
            fi
        else
            echo "$line" >> "$tmp"
        fi
    done < "$file"

    mv "$tmp" "$file"

    # Fix trailing commas (inline _jsonc_fix_trailing_commas)
    local tmp2="${file}.tmp2"
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
    ' "$file" > "$tmp2" || { rm -f "$tmp2"; return 1; }
    mv "$tmp2" "$file"
    return 0
}
