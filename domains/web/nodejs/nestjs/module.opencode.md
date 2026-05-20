---
version: "2.1"
module:
  id: "web.nodejs.nestjs"
  name: "Node.js NestJS"
  version: "1.0.0"
  description: "Node.js NestJS后端框架开发支持"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../../typescript/core/module.opencode.md"

  provides:
    languages: ["typescript"]
    apis: ["nestjs"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    node_versions: ["18", "20", "22"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
