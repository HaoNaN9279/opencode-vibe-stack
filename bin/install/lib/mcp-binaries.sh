# ---- Install MCP Binaries ----
#
# Scans domains/*/mcp/*.json for MCP configs with "release" metadata,
# and downloads the pre-built binary from GitHub Releases.
# Configs without "release" are skipped (binary expected to be already present).
install_mcp_binaries() {
    local vibe_home="$1"

    local plat_key
    case "$(uname -s)" in
        Linux)                         plat_key="linux" ;;
        Darwin)                        plat_key="darwin" ;;
        MINGW*|MSYS*|CYGWIN*)          plat_key="windows" ;;
        *)                             plat_key="linux" ;;
    esac

    echo ""
    local found_any=false

    for json_file in $(find "$vibe_home/domains" -path "*/mcp/*.json" ! -name "README.md" 2>/dev/null | sort); do
        [ ! -f "$json_file" ] && continue

        # Skip files without release metadata
        grep -q '"release"' "$json_file" 2>/dev/null || continue

        # Strip // comments from JSONC
        local content
        content=$(sed 's/[[:space:]]*\/\/.*$//' "$json_file")

        # Extract MCP servers with release metadata (tab-separated: name \t cmd \t repo \t asset)
        echo "$content" | awk -v plat="$plat_key" -v home="$vibe_home" '
        BEGIN { OFS="\t"; srv=""; cmd=""; repo=""; asset=""; in_release=0; in_cmd=0 }

        { gsub(/^[[:space:]]+/, ""); gsub(/,[[:space:]]*$/, "") }

        # Track release block FIRST — must appear before server-entry regex
        # so that "release": { sets in_release before being consumed as a server entry.
        /"release"/ { in_release = 1 }
        in_release && /^\}[[:space:]]*,?[[:space:]]*$/ { in_release = 0 }

        # Server entry: "name": { (skip if inside release block)
        /^"[^"]+"[[:space:]]*:[[:space:]]*\{$/ {
            if (in_release) { next }
            flush()
            srv = $0; gsub(/[[:space:]]*:.*/, "", srv); gsub(/"/, "", srv)
            cmd = ""; repo = ""; asset = ""; in_release = 0; in_cmd = 0
            next
        }

        # Command array on single line: "command": ["path"]
        /"command"/ {
            in_cmd = 1
            if (match($0, /\[[[:space:]]*"([^"]+)"/)) {
                cmd = substr($0, RSTART+1, RLENGTH-1)
                gsub(/^\[[[:space:]]*"/, "", cmd); gsub(/"[[:space:]]*\]?.*$/, "", cmd)
                gsub(/\$\{VIBE_STACK_HOME\}/, home, cmd)
                in_cmd = 0
            }
            next
        }

        # Multi-line command array: "path" on next line
        in_cmd && /^[[:space:]]*"/ {
            gsub(/^[[:space:]]*"/, ""); gsub(/".*/, "")
            cmd = $0
            gsub(/\$\{VIBE_STACK_HOME\}/, home, cmd)
            in_cmd = 0
        }

        in_cmd && /\]/ { in_cmd = 0 }

        # Repo inside release
        in_release && /"repo"/ {
            gsub(/.*"repo"[[:space:]]*:[[:space:]]*"/, "")
            gsub(/".*/, "")
            repo = $0
        }

        # Platform asset inside release
        in_release && repo != "" {
            re = "\"" plat "\""
            if (index($0, re) > 0) {
                gsub(/.*"'"$plat_key"'"[[:space:]]*:[[:space:]]*"/, "")
                gsub(/".*/, "")
                asset = $0
            }
        }

        # End of blocks
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
                echo "  ✅ $srv — binary already installed at $cmd"
                continue
            fi

            local url="https://github.com/$repo/releases/latest/download/$asset"
            echo "  ⬇  $srv: downloading $asset …"
            mkdir -p "$(dirname "$cmd")" 2>/dev/null

            if command -v curl &>/dev/null; then
                if curl -fsSL -o "$cmd" "$url" 2>/dev/null; then
                    chmod +x "$cmd" 2>/dev/null
                    echo "    ✅ $asset installed → $cmd"
                else
                    echo "    ⚠  Download failed: $url"
                    rm -f "$cmd" 2>/dev/null
                fi
            elif command -v wget &>/dev/null; then
                if wget -q -O "$cmd" "$url" 2>/dev/null; then
                    chmod +x "$cmd" 2>/dev/null
                    echo "    ✅ $asset installed → $cmd"
                else
                    echo "    ⚠  Download failed: $url"
                    rm -f "$cmd" 2>/dev/null
                fi
            else
                echo "    ⚠  No curl or wget found — cannot download: $url"
            fi
        done
    done

    if ! $found_any; then
        echo "  ℹ  No MCP binaries to download (all already installed or no release metadata)."
    fi
    echo ""
}
