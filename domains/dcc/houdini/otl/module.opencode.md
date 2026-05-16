---
version: "2.1"
module:
  id: "dcc.houdini.otl"
  name: "Houdini OTL Assets"
  version: "1.0.0"
  description: "Houdini OTL数字资产开发支持"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../vex/module.opencode.md"

  provides:
    apis: ["houdini-otl"]
    tools: ["otl-builder"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    houdini_versions: ["19.5", "20.0", "20.5"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
