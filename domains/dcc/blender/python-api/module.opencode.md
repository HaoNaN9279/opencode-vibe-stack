---
version: "2.1"
module:
  id: "dcc.blender.python-api"
  name: "Blender Python API"
  version: "1.0.0"
  description: "Blender Python API开发支持"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../core/module.opencode.md"

  provides:
    languages: ["python"]
    apis: ["blender-python"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    blender_versions: ["3.6", "4.0", "4.1", "4.2"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
