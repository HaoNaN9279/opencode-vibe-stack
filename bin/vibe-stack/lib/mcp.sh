# ---- MCP Activation ----
#
# activate_mcp <mcp_src_dir> <domain_name> <vibe_stack_home> <project_root>
#
# Scans mcp/*.json in the domain's mcp/ directory (OpenCode native "mcp" format),
# resolves ${VIBE_STACK_HOME} / ${PROJECT_ROOT} placeholders,
# adds "vibe:" prefix to server names for namespace isolation,
# and merges entries into .opencode/opencode.json under the "mcp" key.
# OpenCode auto-discovers mcp entries from .opencode/opencode.json on startup.
activate_mcp() {
    local mcp_src="$1"
    local domain="$2"
    local vibe_home="$3"
    local project_root="$4"

    local json_files
    json_files=$(ls "$mcp_src"/*.json 2>/dev/null || true)
    [ -z "$json_files" ] && return 0

    mkdir -p ".opencode"
    local project_config=".opencode/opencode.json"

    # Step 1: Extract MCP server entries from source files into a temp list
    # Format per line: vibe:name<TAB><raw JSON config block (single line)>
    local mcp_tmp
    mcp_tmp=$(mktemp)

    for f in $json_files; do
        local normalized_home
        normalized_home=$(echo "$vibe_home" | sed 's/\\/\//g')
        awk -v vibe_home="$normalized_home" -v project_root="$project_root" '
        BEGIN { in_mcp=0; server=""; depth=0; buf="" }

        # Strip comments and leading whitespace only.
        # Do NOT strip trailing commas -- they are essential for valid JSON
        # when lines are later concatenated into the config blob.
        { gsub(/\/\/.*$/, ""); gsub(/^[[:space:]]+/, "") }

        /^"mcp"/ || /^"mcpServers"/ { in_mcp=1; next }

        # Guard with server == "" to prevent nested "key": { from overwriting
        # the outer server name (e.g. "asset": { inside "data-forge": {).
        in_mcp && server == "" && /^"[^"]+"[[:space:]]*:[[:space:]]*\{/ {
            server = $0
            gsub(/[[:space:]]*:.*/, "", server)
            gsub(/"/, "", server)
            # Strip server name prefix so buf starts from "{" not "key": {.
            sub(/^"[^"]+"[[:space:]]*:[[:space:]]*/, "", $0)
            depth = 0
            buf = ""
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
                gsub(/\$\{PROJECT_ROOT\}/, project_root, buf)
                gsub(/[[:space:]]+$/, "", buf)
                printf "vibe:%s\t%s\n", server, buf
                server = ""; buf = ""
            }
        }
        ' "$f" >> "$mcp_tmp"
    done

    [ ! -s "$mcp_tmp" ] && { rm -f "$mcp_tmp"; return 0; }

    # Step 2: Merge into opencode.json
    # Strategy: find mcp block boundaries, rebuild mcp section with non-vibe entries + new entries
    #
    # Touch config file before awk reads it. Without this, GNU awk treats a
    # missing input file as a fatal error, suppresses its END block entirely,
    # produces no output, and can leave an orphaned ${project_config}.tmp.
    touch "$project_config" 2>/dev/null || true

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
            in_mcp = 1
            depth = 0
            if ($0 ~ /\{/) depth++
            # Skip the original mcp opening line
            next
        }
        else if ($0 ~ /^[[:space:]]*\}/ && !found_end && !in_mcp) {
            # Last closing brace — possible insertion point if no mcp exists
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
            # End of original mcp block — output rebuilt mcp section
            print "  \"mcp\": {"
            for (i = 1; i <= n_new; i++) {
                comma = (i < n_new) ? "," : ""
                # new_configs keyed by string name, not numeric index
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
            # File had no mcp key — insert before closing }
            print "  \"mcp\": {"
            for (i = 1; i <= n_new; i++) {
                comma = (i < n_new) ? "," : ""
                print "    \"" new_names[i] "\": " new_configs[new_names[i]] comma
            }
            print "  }"
            print end_line
        }
        else if (!in_mcp && !found_mcp && !found_end) {
            # File was empty or minimal — create from scratch
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
    ' "$project_config" > "${project_config}.tmp" 2>/dev/null

    if [ -s "${project_config}.tmp" ]; then
        _jsonc_fix_trailing_commas "${project_config}.tmp"
        mv "${project_config}.tmp" "$project_config"
        ok "MCP activated -> $project_config"
        while IFS= read -r line; do
            local srv_name="${line%%$'\t'*}"
            [ -n "$srv_name" ] && info "    + $srv_name"
        done < "$mcp_tmp"
    else
        warn "MCP activation: failed to merge into $project_config"
        rm -f "${project_config}.tmp"
    fi

    rm -f "$mcp_tmp"
}

# deactivate_mcp <domain_name> <domain_root>
#
# Scans domain_root/mcp/*.json to find original server names,
# then removes vibe:{name} entries from .opencode/opencode.json.
deactivate_mcp() {
    local domain="$1"
    local domain_root="$2"

    local project_config=".opencode/opencode.json"
    [ ! -f "$project_config" ] && return 0

    local mcp_src="$domain_root/mcp"
    [ ! -d "$mcp_src" ] && return 0

    local json_files
    json_files=$(ls "$mcp_src"/*.json 2>/dev/null || true)
    [ -z "$json_files" ] && return 0

    # Collect server names from MCP source files
    local target_names=""
    for f in $json_files; do
        # Extract server names from "mcp" or "mcpServers" block
        local names
        names=$(awk '
        /"mcp"/ || /"mcpServers"/ { in_mcp=1; depth=0; next }
        # Only capture top-level server keys (depth==0), skip nested objects.
        in_mcp && depth == 0 && /^[[:space:]]*"[^"]+"[[:space:]]*:[[:space:]]*\{/ {
            s = $0; gsub(/^[[:space:]]*"/, "", s); gsub(/".*/, "", s)
            print "vibe:" s
        }
        # Track brace depth to distinguish top-level from nested keys.
        {
            n = split($0, chs, "")
            for (i = 1; i <= n; i++) {
                if (chs[i] == "{") depth++
                if (chs[i] == "}") depth--
            }
        }
        /^\}[[:space:]]*,?[[:space:]]*$/ { if (in_mcp && depth == 0) in_mcp=0 }
        ' "$f" 2>/dev/null)
        target_names="${target_names}${target_names:+$'\n'}${names}"
    done

    [ -z "$target_names" ] && return 0

    # Remove vibe:* entries from opencode.json mcp block
    awk -v targets="$target_names" '
    BEGIN {
        split(targets, target_arr, "\n")
        for (i in target_arr) {
            if (target_arr[i] != "") target_set[target_arr[i]] = 1
        }
    }

    !in_mcp {
        if ($0 ~ /^[[:space:]]*"mcp"/) {
            in_mcp = 1
            depth = 0
            if ($0 ~ /\{/) depth++
            print
            next
        }
        print
        next
    }

    {
        opens = gsub(/{/, "{", $0)
        closes = gsub(/}/, "}", $0)
        new_depth = depth + opens - closes

        if (skipping && new_depth <= skip_target) {
            skipping = 0
        }

        if (!skipping) {
            if (depth == 1 && $0 ~ /"vibe:[^"]*"/) {
                s = $0; gsub(/^[[:space:]]*"/, "", s); gsub(/".*/, "", s)
                if (s in target_set) {
                    skipping = 1; skip_target = new_depth
                    depth = new_depth; next
                }
            }
            if (new_depth == 0) {
                in_mcp = 0
            }
            print
        }

        depth = new_depth
    }
    ' "$project_config" > "${project_config}.tmp" 2>/dev/null

    if [ -s "${project_config}.tmp" ]; then
        _jsonc_fix_trailing_commas "${project_config}.tmp"
        mv "${project_config}.tmp" "$project_config"
        ok "MCP deactivated for $domain:"
        while IFS= read -r name; do
            [ -n "$name" ] && info "    - $name"
        done <<< "$target_names"
    else
        warn "MCP deactivation: failed to process $project_config"
        rm -f "${project_config}.tmp"
    fi
}

install_mcp_binaries() {
    local vibe_home="$1"

    local plat_key
    case "$(uname -s)" in
        Linux)  plat_key="linux" ;;
        Darwin) plat_key="darwin" ;;
        *)      plat_key="linux" ;;
    esac

    local found_any=false

    for json_file in $(find "$vibe_home/domains" -path "*/mcp/*.json" ! -name "README.md" 2>/dev/null | sort); do
        [ ! -f "$json_file" ] && continue
        grep -q '"release"' "$json_file" 2>/dev/null || continue

        local content
        content=$(sed 's/[[:space:]]*\/\/.*$//' "$json_file")

        local normalized_home
        normalized_home=$(echo "$vibe_home" | sed 's/\\/\//g')
        echo "$content" | awk -v plat="$plat_key" -v home="$normalized_home" '
        BEGIN { OFS="\t"; srv=""; cmd=""; repo=""; asset=""; in_release=0; in_cmd=0 }

        { gsub(/^[[:space:]]+/, ""); gsub(/,[[:space:]]*$/, "") }

        /^"[^"]+"[[:space:]]*:[[:space:]]*\{$/ {
            flush()
            srv = $0; gsub(/[[:space:]]*:.*/, "", srv); gsub(/"/, "", srv)
            cmd = ""; repo = ""; asset = ""; in_release = 0; in_cmd = 0
            next
        }

        /"command"/ {
            in_cmd = 1
            start = index($0, "[")
            if (start > 0) {
                rest = substr($0, start+1)
                if (match(rest, /"([^"]+)"/)) {
                    cmd = substr(rest, RSTART+1, RLENGTH-2)
                    gsub(/\$\{VIBE_STACK_HOME\}/, home, cmd)
                    in_cmd = 0
                }
            }
            next
        }

        in_cmd && /^[[:space:]]*"/ {
            gsub(/^[[:space:]]*"/, ""); gsub(/".*/, "")
            cmd = $0
            gsub(/\$\{VIBE_STACK_HOME\}/, home, cmd)
            in_cmd = 0
        }

        in_cmd && /\]/ { in_cmd = 0 }
        /"release"/ { in_release = 1 }

        in_release && /"repo"/ {
            gsub(/.*"repo"[[:space:]]*:[[:space:]]*"/, "")
            gsub(/".*/, "")
            repo = $0
        }

        in_release && repo != "" {
            if (index($0, "\"" plat "\"") > 0) {
                gsub(/.*"/, "", $0)
                gsub(/"[:[space:]]*/, "", $0)
                gsub(/".*/, "")
                asset = $0
            }
        }

        /^\}[[:space:]]*,?[[:space:]]*$/ {
            if (in_release) { in_release = 0 }
            else { flush(); srv = "" }
        }

        function flush() {
            if (srv && cmd && repo && asset)
                print srv, cmd, repo, asset
        }

        END { flush() }
        ' | while IFS=$'\t' read -r srv cmd repo asset; do
            [ -z "$srv" ] && continue
            found_any=true

            if [ -f "$cmd" ]; then
                info "$srv — already installed"
                continue
            fi

            local url="https://github.com/$repo/releases/latest/download/$asset"
            info "$srv: downloading $asset …"
            mkdir -p "$(dirname "$cmd")" 2>/dev/null

            if command -v curl &>/dev/null; then
                if curl -fsSL -o "$cmd" "$url" 2>/dev/null; then
                    chmod +x "$cmd" 2>/dev/null
                    ok "$asset installed -> $cmd"
                else
                    warn "Download failed: $url"
                    rm -f "$cmd" 2>/dev/null
                fi
            elif command -v wget &>/dev/null; then
                if wget -q -O "$cmd" "$url" 2>/dev/null; then
                    chmod +x "$cmd" 2>/dev/null
                    ok "$asset installed -> $cmd"
                else
                    warn "Download failed: $url"
                    rm -f "$cmd" 2>/dev/null
                fi
            else
                warn "No curl/wget — cannot download: $url"
            fi
        done
    done

    if ! $found_any; then
        info "No MCP binaries to download."
    fi
}
