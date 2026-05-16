---
version: "2.1"
combination:
  id: "combination.unity-toolchain"
  name: "Unity工具链"
  version: "1.0.0"
  description: "完整的Unity游戏开发工具链，包含编辑器扩展、性能优化和CI/CD支持"

  domains:
    - "game-engine.unity.csharp-api"
    - "game-engine.unity.ecs"
    - "game-engine.unity.burst"
    - "game-engine.unity.editor"
    - "desktop.csharp.wpf"
    - "web.nodejs.express"

  default_agent: "unity-toolchain.orchestrator"

imports:
  - "./agents/*.opencode.md"
---
