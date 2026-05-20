---
# domains/dcc/blender/plugins/module.opencode.md
version: "2.1"
module:
  id: "dcc.blender.plugins"
  name: "Blender Plugins"
  version: "1.0.0"
  description: "Blender Plugins支持"
  
  dependencies:
    - "../../../core/config.opencode.md"
    - "../core/module.opencode.md"
  
  provides:
    languages: ["python"]
    apis: ["blender-python"]

# 自动导入本模块的所有资源
imports:
  - "./skills/*.opencode.md"
  - "./rules/*.opencode.md"
  - "./templates/*.opencode.md"
  - "./mcp/*.opencode.md"
  - "./agents/*.opencode.md"
---