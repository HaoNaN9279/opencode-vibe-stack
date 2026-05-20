---
version: "2.1"
module:
  id: "desktop.pyqt"
  name: "Python PyQt Desktop"
  version: "1.0.0"
  description: "Python PyQt/PySide桌面应用开发支持"

  dependencies:
    - "../../../core/config.opencode.md"

  provides:
    languages: ["python"]
    apis: ["pyqt", "pyside"]

  compatibility:
    platforms: ["windows", "linux", "macos"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
