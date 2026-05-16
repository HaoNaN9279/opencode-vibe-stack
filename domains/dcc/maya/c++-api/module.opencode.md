---
version: "2.1"
module:
  id: "dcc.maya.c++-api"
  name: "Maya C++ API"
  version: "1.0.0"
  description: "Maya C++插件和扩展开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["c++"]
    apis: ["maya-cpp"]

  compatibility:
    platforms: ["windows", "linux"]
    maya_versions: ["2023", "2024", "2025"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
