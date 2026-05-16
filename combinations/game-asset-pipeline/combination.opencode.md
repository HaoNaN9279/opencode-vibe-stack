---
version: "2.1"
combination:
  id: "combination.game-asset-pipeline"
  name: "游戏资产管线"
  version: "1.0.0"
  description: "完整的游戏资产管线工具链，覆盖DCC导出、引擎导入、桌面工具和后端服务"

  domains:
    - "dcc.houdini.hdk"
    - "dcc.houdini.vex"
    - "dcc.houdini.python-api"
    - "dcc.maya.python-api"
    - "dcc.blender.python-api"
    - "game-engine.unity.csharp-api"
    - "game-engine.unity.editor"
    - "game-engine.unreal.c++-api"
    - "desktop.csharp.wpf"
    - "web.nodejs.express"

  default_agent: "game-asset-pipeline.orchestrator"

imports:
  - "./agents/*.opencode.md"
  - "./orchestrations/*.opencode.md"
---
