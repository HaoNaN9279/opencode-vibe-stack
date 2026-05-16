---
version: "2.1"
mcp_server:
  name: "filesystem"
  type: "builtin"
  description: "文件系统操作"

  capabilities:
    - "read-file"
    - "write-file"
    - "list-directory"
    - "search-files"
    - "file-metadata"
---
