---
version: "2.1"
module:
  id: "game-engine.unreal.blueprint"
  name: "Unreal Blueprint"
  version: "1.0.0"
  description: "Unreal Engine蓝图系统支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    apis: ["unreal-blueprint"]
    tools: ["blueprint-editor"]

  compatibility:
    platforms: ["windows", "linux"]
    unreal_versions: ["5.3", "5.4", "5.5"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
