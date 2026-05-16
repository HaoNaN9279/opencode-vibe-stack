---
version: "2.1"
module:
  id: "web.nodejs.express"
  name: "Node.js Express"
  version: "1.0.0"
  description: "Node.js Express后端API开发支持"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../../typescript/core/module.opencode.md"

  provides:
    languages: ["typescript", "javascript"]
    apis: ["express", "nodejs"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    node_versions: ["18", "20", "22"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
