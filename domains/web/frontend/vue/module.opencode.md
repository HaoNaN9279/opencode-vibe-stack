---
version: "2.1"
module:
  id: "web.frontend.vue"
  name: "Vue Frontend"
  version: "1.0.0"
  description: "Vue.js前端框架开发支持"

  dependencies:
    - "../../../core/config.opencode.md"
    - "../../typescript/core/module.opencode.md"

  provides:
    languages: ["typescript", "javascript", "vue"]
    apis: ["vue"]

  compatibility:
    platforms: ["windows", "linux", "macos"]

imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---
