---
version: "2.1"
module:
  id: "desktop.cpp.qt"
  name: "C++ Qt Desktop"
  version: "1.0.0"
  description: "C++ Qt桌面应用开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["c++"]
    apis: ["qt"]

  compatibility:
    platforms: ["windows", "linux", "macos"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
