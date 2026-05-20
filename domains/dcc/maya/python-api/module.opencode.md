---
version: "2.1"
module:
  id: "dcc.maya.python-api"
  name: "Maya Python API"
  version: "1.0.0"
  description: "Maya Python API (pymel, maya.cmds) 开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["python"]
    apis: ["maya-python"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    maya_versions: ["2023", "2024", "2025"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
