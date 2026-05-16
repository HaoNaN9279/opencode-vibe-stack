---
version: "2.1"
module:
  id: "web.frontend.react"
  name: "React Frontend"
  version: "1.0.0"
  description: "React前端框架开发支持"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../../typescript/core/module.opencode.md"

  provides:
    languages: ["typescript", "javascript", "tsx"]
    apis: ["react"]

  compatibility:
    platforms: ["windows", "linux", "macos"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
