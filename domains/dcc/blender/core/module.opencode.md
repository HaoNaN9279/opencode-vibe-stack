---
version: "2.1"
module:
  id: "dcc.blender.core"
  name: "Blender Core"
  version: "1.0.0"
  description: "Blender通用基础支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["python"]
    apis: ["blender-core"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    blender_versions: ["3.6", "4.0", "4.1", "4.2"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
