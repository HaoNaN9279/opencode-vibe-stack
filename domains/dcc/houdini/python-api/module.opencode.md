---
version: "2.1"
module:
  id: "dcc.houdini.python-api"
  name: "Houdini Python API"
  version: "1.0.0"
  description: "Houdini Python API开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["python"]
    apis: ["houdini-python"]

  compatibility:
    platforms: ["windows", "linux", "macos"]
    houdini_versions: ["19.5", "20.0", "20.5"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
