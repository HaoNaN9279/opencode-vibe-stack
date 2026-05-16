---
version: "2.1"
combination:
  id: "combination.dcc-plugin-suite"
  name: "DCC插件套件"
  version: "1.0.0"
  description: "跨DCC软件的插件开发工具链"

  domains:
    - "dcc.blender.python-api"
    - "dcc.blender.c++-api"
    - "dcc.houdini.hdk"
    - "dcc.houdini.python-api"
    - "dcc.maya.python-api"
    - "dcc.maya.c++-api"
    - "desktop.csharp.wpf"

  default_agent: "dcc-plugin-suite.orchestrator"

imports:
  - "./agents/*.opencode.md"
---
