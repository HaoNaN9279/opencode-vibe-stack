---
version: "2.1"
combinator:
  conflict_resolution: "workspace-override"
  priority:
    - "workspace"
    - "combinations"
    - "domains"
    - "core"
  lazy_load: true

  resolution_strategy:
    skills: "merge-rename-on-conflict"
    agents: "prefer-higher-priority"
    rules: "merge-all"
    mcp_servers: "merge-all"
    templates: "prefer-workspace"
---
