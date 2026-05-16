---
version: "2.1"
platform: "linux"

env:
  OPCODE_CONFIG_DIR: "~/.config/opencode/User"

npm:
  registry: "https://registry.npmmirror.com"

python:
  pip_index: "https://pypi.tuna.tsinghua.edu.cn/simple"

mcp_servers:
  - id: "linux-shell"
    type: "builtin"
    capabilities:
      - "bash-execution"
      - "systemd-service"
---
