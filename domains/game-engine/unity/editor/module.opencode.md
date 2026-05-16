---
version: "2.1"
module:
  id: "game-engine.unity.editor"
  name: "Unity Editor Extensions"
  version: "1.0.0"
  description: "Unity编辑器扩展开发支持（Editor Window, Toolbar, Inspector等）"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../csharp-api/module.opencode.md"

  provides:
    languages: ["c#"]
    apis: ["unity-editor"]

  compatibility:
    platforms: ["windows", "macos"]
    unity_versions: ["2021.3", "2022.3", "2023.3", "2026.1"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
