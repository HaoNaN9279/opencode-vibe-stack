---
version: "2.1"
mcp_server:
  name: "docsetmcp"
  type: "local"
  command: "uvx"
  args: ["docsetmcp"]
  description: "Dash/Zeal 离线文档查询"
  capabilities:
    - "search-docs"
    - "list-docsets"
    - "list-entries"
    - "fetch-cheatsheet"
---
