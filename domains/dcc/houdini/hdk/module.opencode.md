---
version: "2.1"
module:
  id: "dcc.houdini.hdk"
  name: "Houdini HDK"
  version: "1.0.0"
  description: "Houdini HDK C++插件开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["c++"]
    apis: ["houdini-hdk"]

  compatibility:
    platforms: ["windows", "linux"]
    houdini_versions: ["19.5", "20.0", "20.5"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
