---
version: "2.1"
module:
  id: "desktop.csharp.winui"
  name: "C# WinUI Desktop"
  version: "1.0.0"
  description: "C# WinUI 3桌面应用开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["c#", "xaml"]
    apis: ["winui"]

  compatibility:
    platforms: ["windows"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
