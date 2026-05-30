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

# ---- Nested JSONC Array Operations ----

# _jsonc_nested_array_add <file> <parent_key> <child_key> <value>
# Returns: 0=added, 1=parent not found, 2=already exists
_jsonc_nested_array_add() {
    local file="$1" parent_key="$2" child_key="$3" val="$4"
    local tmp="${file}.tmp"
    [ ! -f "$file" ] && return 1
    if ! grep -q "\"$parent_key\"" "$file" 2>/dev/null; then return 1; fi
    awk -v pk="$parent_key" -v ck="$child_key" -v val="$val" '
    BEGIN { s=0; d=0; hc=0; ins=0; e=0 }
    {
        if (!ins && !e) {
            if (s==0 && $0 ~ "\"" pk "\"") { s=1; d=0 }
            if (s>=1) {
                if (s==1 && $0 ~ "\"" ck "\"") { s=2; hc=1 }
                n=split($0,c,""); for(i=1;i<=n;i++){ if(c[i]=="{") d++; if(c[i]=="}") d-- }
                if (s==2) {
                    if (hc==1 && $0 ~ /\]/) {
                        if (match($0, /\[[^]]*\]/)) { ac=substr($0,RSTART+1,RLENGTH-2); if (index(ac,val)>0) e=1 }
                    } else if (index($0,val)>0 && $0 !~ "\"" ck "\"") { e=1 }
                    if (!ins && !e) {
                        if ($0 ~ /^[[:space:]]*][[:space:]]*,?[[:space:]]*$/) { print "      " val ","; ins=1 }
                        else if ($0 ~ /\]/) {
                            sub(/\]/, ($0 ~ /\[[[:space:]]*\]/ ? val "&" : ", " val "&"), $0); ins=1
                        }
                    }
                }
                if (s==1 && d==0 && !ins && !e) { if (!hc) { print "    \"" ck "\": ["; print "      " val; print "    ]" }; ins=1 }
            }
        }
        print
    }
    END { if (e) exit 2; if (ins) exit 0; exit 1 }
    ' "$file" > "$tmp"
    local rc=$?
    if [ $rc -eq 0 ]; then mv "$tmp" "$file"; _jsonc_fix_trailing_commas "$file"
    else rm -f "$tmp"; fi
    return $rc
}

# _jsonc_nested_array_remove <file> <parent_key> <child_key> <value>
# Returns: 0=removed, 1=not found
_jsonc_nested_array_remove() {
    local file="$1" parent_key="$2" child_key="$3" val="$4"
    local tmp="${file}.tmp"
    [ ! -f "$file" ] && return 1
    awk -v pk="$parent_key" -v ck="$child_key" -v val="$val" '
    BEGIN { s=0; d=0; ia=0; ad=0; f=0 }
    {
        if (s<3) {
            if (s==0 && $0 ~ "\"" pk "\"") { s=1; d=0 }
            if (s>=1) {
                if (s==1 && $0 ~ "\"" ck "\"") { s=2; ia=0; ad=0 }
                n=split($0,c,""); for(i=1;i<=n;i++){ if(c[i]=="{") d++; if(c[i]=="}") d-- }
                if (s==2) {
                    n=split($0,c,""); for(i=1;i<=n;i++){ if(c[i]=="[") { ia=1; ad++ }; if(c[i]=="]") ad-- }
                    if (ia && index($0,val)>0) { f=1; next }
                    if (ia && ad<=0) s=1
                }
                if (s==1 && d==0) s=3
            }
        }
        print
    }
    END { exit f ? 0 : 1 }
    ' "$file" > "$tmp"
    local rc=$?
    if [ $rc -eq 0 ]; then mv "$tmp" "$file"; _jsonc_fix_trailing_commas "$file"
    else rm -f "$tmp"; fi
    return $rc
}
