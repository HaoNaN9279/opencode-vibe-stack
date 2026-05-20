---
version: "2.1"
mcp_server:
  name: "docsetmcp"
  type: "local"
  command: "uvx"
  args: ["docsetmcp"]
  env:
    DOCSET_PATH: "/mnt/d/workspace/docsets"
    CHEATSHEET_PATH: "/mnt/d/workspace/cheatsheets"
  description: "Dash/Zeal 离线文档查询"
  capabilities:
    - "search-docs"
    - "list-docsets"
    - "list-entries"
    - "fetch-cheatsheet"
---
