---
version: "2.1"
agent:
  id: "dcc-plugin-suite.orchestrator"
  name: "DCC插件套件编排器"
  type: "composite-orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-dcc-plugin-development"]

    composes:
      - "blender.python.orchestrator"
      - "houdini.hdk.orchestrator"
      - "desktop.csharp.wpf.orchestrator"

  task_flows:
    "create-cross-dcc-plugin":
      description: "在多个DCC软件中创建功能一致的插件"
      steps:
        - name: "定义公共API接口"
          agent: "core.dynamic-orchestrator"
          task: "design-cross-dcc-api"
        - name: "实现Blender版本"
          agent: "blender.python.code-generator"
          task: "implement-blender-plugin"
        - name: "实现Houdini版本"
          agent: "houdini.hdk.code-generator"
          task: "implement-houdini-plugin"
        - name: "开发通用桌面配置工具"
          agent: "desktop.csharp.wpf.code-generator"
          task: "implement-config-tool"

  persona: |
    你是一位跨DCC平台的插件开发专家。
    你熟悉Blender、Houdini、Maya的插件体系。
    你擅长设计跨软件统一的工具接口。
---
