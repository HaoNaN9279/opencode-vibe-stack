from pathlib import Path

# 领域目录类型列表（每个领域包含的子目录）
VIBE_STACK_DIR_TYPES = ["rules", "agents", "commands", "mcp", "skills", "tools"]

# OpenCode 用户配置根目录
OPENCODE_CONFIG_DIR = Path.home() / ".config" / "opencode"

# MCP 注册表文件路径（用户级）
VIBE_STACK_MCP_REGISTRY_PATH = OPENCODE_CONFIG_DIR / "vibe-stack-mcp.jsonc"

# 激活清单文件名（项目级）
ACTIVE_MANIFEST_NAME = ".vibe-stack-active.json"

# OhMyOpenAgent 配置文件名
OMO_CONFIG_NAME = "oh-my-openagent.jsonc"

# OpenCode 配置文件名
OPECODE_CONFIG_NAME = "opencode.json"

# Core MCP 条目前缀（写入 opencode.json 时使用）
MCP_CORE_PREFIX = "vibe:core-"

# Domain MCP 条目前缀（写入 opencode.json 时使用）
MCP_DOMAIN_PREFIX = "vibe:"

# MCP 符号链接目录占位符（在 MCP JSON 配置中引用）
MCP_LINK_DIR_PLACEHOLDER = "${MCP_LINK_DIR}"
