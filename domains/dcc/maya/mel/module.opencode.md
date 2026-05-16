---
version: "2.1"
module:
  id: "dcc.maya.mel"
  name: "Maya MEL Language"
  version: "1.0.0"
  description: "Maya MEL脚本语言支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["mel"]
    apis: ["maya-mel"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    maya_versions: ["2023", "2024", "2025"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
