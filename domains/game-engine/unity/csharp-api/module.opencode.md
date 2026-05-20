---
version: "2.1"
module:
  id: "game-engine.unity.csharp-api"
  name: "Unity C# API"
  version: "1.0.0"
  description: "Unity C#脚本开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["c#"]
    apis: ["unity-csharp"]

  compatibility:
    platforms: ["windows", "macos"]
    unity_versions: ["2021.3", "2022.3", "2023.3", "2026.1"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
