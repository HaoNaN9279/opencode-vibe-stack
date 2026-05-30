# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ---- Helpers ----

die() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
warn() { echo -e "${YELLOW}[warn]${NC} $*" >&2; }
info() { echo -e "${CYAN}[i]${NC} $*"; }
ok() { echo -e "${GREEN}[OK]${NC} $*"; }

# Resolve ~ in path strings
resolve_path() {
    local p="$1"
    if [[ "$p" == "~"* ]]; then
        echo "${HOME}${p#\~}"
    else
        echo "$p"
    fi
}
