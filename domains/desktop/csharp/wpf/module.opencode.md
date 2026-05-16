---
version: "2.1"
module:
  id: "desktop.csharp.wpf"
  name: "C# WPF Desktop"
  version: "1.0.0"
  description: "C# WPF桌面应用开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["c#", "xaml"]
    apis: ["wpf"]

  compatibility:
    platforms: ["windows"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
---
