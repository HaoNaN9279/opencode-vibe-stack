---
version: "2.1"
module:
  id: "game-engine.unreal.c++-api"
  name: "Unreal Engine C++ API"
  version: "1.0.0"
  description: "Unreal Engine C++开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["c++"]
    apis: ["unreal-cpp"]

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
