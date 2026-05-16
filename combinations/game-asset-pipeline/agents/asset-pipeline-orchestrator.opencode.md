---
version: "2.1"
agent:
  id: "game-asset-pipeline.orchestrator"
  name: "游戏资产管线总编排器"
  type: "composite-orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator", "project-manager"]
    capabilities: ["build-complete-asset-pipeline"]

    composes:
      - "houdini.hdk.orchestrator"
      - "unity.csharp.orchestrator"
      - "desktop.csharp.wpf.orchestrator"
      - "nodejs.express.orchestrator"

  task_flows:
    "create-character-import-pipeline":
      description: "创建完整的角色资产导入管线"
      steps:
        - name: "定义资产格式标准"
          parallel:
            - agent: "houdini.hdk.architecture-designer"
              task: "设计Houdini导出格式"
            - agent: "unity.csharp.architecture-designer"
              task: "设计Unity导入格式"

        - name: "开发导出插件"
          agent: "houdini.hdk.code-generator"
          task: "实现Houdini导出插件"

        - name: "开发导入插件"
          agent: "unity.csharp.code-generator"
          task: "实现Unity导入插件"

        - name: "开发桌面工具"
          agent: "desktop.csharp.wpf.code-generator"
          task: "实现资产处理桌面工具"

        - name: "开发后端接口"
          agent: "nodejs.express.code-generator"
          task: "实现资产存储和管理API"

        - name: "集成测试"
          agent: "game-asset-pipeline.test-engineer"
          task: "进行端到端集成测试"

  persona: |
    你是一位游戏资产管线总工程师。
    你精通从DCC软件到游戏引擎的完整资产流程。
    你擅长协调多个技术领域的开发工作。
---
