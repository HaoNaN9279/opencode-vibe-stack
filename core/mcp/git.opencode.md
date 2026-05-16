---
version: "2.1"
mcp_server:
  name: "git"
  type: "builtin"
  description: "Git版本控制操作"

  capabilities:
    - "git-status"
    - "git-diff"
    - "git-log"
    - "git-commit"
    - "git-branch"
    - "git-push-pull"
---
