---
version: "2.1"
module:
  id: "web.typescript.core"
  name: "TypeScript Core"
  version: "1.0.0"
  description: "TypeScript语言核心支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["typescript"]
    apis: ["typescript"]

  compatibility:
    platforms: ["windows", "linux", "macos"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
