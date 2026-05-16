---
version: "2.1"
platform: "wsl2"

env:
  OPCODE_CONFIG_DIR: "~/.config/opencode/User"
  WSLENV: "OPCODE_STACK_ROOT/up:WORKSPACE_ROOT/up"

interop:
  windows_path_mapping: "/mnt/c"
  enable_windows_interop: true

npm:
  registry: "https://registry.npmmirror.com"

python:
  pip_index: "https://pypi.tuna.tsinghua.edu.cn/simple"

mcp_servers:
  - id: "wsl-interop"
    type: "builtin"
    capabilities:
      - "windows-path-resolution"
      - "cross-fs-access"
---
