# ---- Path/Platform Helpers ----

# Convert a POSIX path to Windows format (/c/Users/... -> C:\Users\...)
posix_to_win() {
    local path="$1"
    if command -v cygpath &>/dev/null; then
        cygpath -wa "$path" 2>/dev/null && return
    fi
    echo "$path" | sed 's|^/\([a-zA-Z]\)/|\1:\\|; s|/|\\|g'
}

# Create a directory link: symlink on Linux/macOS, junction on Windows.
# On MSYS2/Cygwin, uses PowerShell junction FIRST to avoid ln -s silently
# copying large directory trees. NEVER falls back to copying.
# Returns 0 on success, 1 on failure.
create_dir_link() {
    local src="$1"
    local dest="$2"

    # Remove existing safely (handles junctions on Windows)
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        case "$OSTYPE" in
            msys|cygwin)
                # rm (without -r) removes symlinks/junctions without following them
                rm -f "$dest" 2>/dev/null || true
                ;;
            *)
                rm -rf "$dest" 2>/dev/null || true
                ;;
        esac
    fi

    # MSYS2/Cygwin: try junction first (no admin, no Developer Mode needed).
    # ln -s on MSYS2 without Developer Mode silently COPIES directories —
    # we skip it entirely to avoid wasteful copy+delete for large trees.
    case "$OSTYPE" in
        msys|cygwin)
            local win_src win_dest
            win_src="$(posix_to_win "$src")"
            win_dest="$(posix_to_win "$dest")"
            if [ -n "$win_src" ] && [ -n "$win_dest" ]; then
                if powershell -NoProfile -Command \
                    "New-Item -ItemType Junction -Path '$win_dest' -Target '$win_src' -Force | Out-Null" \
                    2>/dev/null; then
                    return 0
                fi
            fi
            # Junction failed — fall through to ln -s as last resort
            ;;
    esac

    # Native symlink (Linux/macOS primary, Windows fallback)
    if ln -s "$src" "$dest" 2>/dev/null; then
        if [ -L "$dest" ]; then
            return 0
        fi
        # MSYS2 silently copied — undo the copy
        case "$OSTYPE" in
            msys|cygwin)
                rm -rf "$dest" 2>/dev/null || true
                ;;
        esac
    fi

    return 1
}
