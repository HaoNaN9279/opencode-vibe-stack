---
version: "2.1"
module:
  id: "game-engine.unreal.editor"
  name: "Unreal Editor Extensions"
  version: "1.0.0"
  description: "Unreal Engine编辑器扩展和工具开发支持"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../c++-api/module.opencode.md"

  provides:
    languages: ["c++"]
    apis: ["unreal-editor"]

  compatibility:
    platforms: ["windows", "linux"]
    unreal_versions: ["5.3", "5.4", "5.5"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
