---
version: "2.1"
module:
  id: "dcc.houdini.vex"
  name: "Houdini VEX Language"
  version: "1.0.0"
  description: "Houdini VEX编程语言支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["vex"]
    apis: ["houdini-vex"]
    tools: ["vex-editor"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    houdini_versions: ["19.5", "20.0", "20.5"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
