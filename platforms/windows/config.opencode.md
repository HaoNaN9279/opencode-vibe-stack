---
version: "2.1"
platform: "windows"

env:
  OPCODE_CONFIG_DIR: "%APPDATA%\\OpenCode\\User"
  DOTNET_ROOT: "${LOCALAPPDATA}\\Microsoft\\dotnet"

npm:
  registry: "https://registry.npmmirror.com"

dotnet:
  nuget_sources:
    - name: "Azure China"
      url: "https://nuget.cdn.azure.cn/v3/index.json"

python:
  pip_index: "https://pypi.tuna.tsinghua.edu.cn/simple"

mcp_servers:
  - id: "windows-shell"
    type: "builtin"
    capabilities:
      - "powershell-execution"
      - "registry-access"
      - "wmi-query"
---
