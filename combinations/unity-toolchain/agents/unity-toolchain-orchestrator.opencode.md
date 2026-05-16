---
version: "2.1"
agent:
  id: "unity-toolchain.orchestrator"
  name: "Unity工具链编排器"
  type: "composite-orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-unity-toolchain"]

    composes:
      - "unity.csharp.orchestrator"
      - "desktop.csharp.wpf.orchestrator"
      - "nodejs.express.orchestrator"

  task_flows:
    "create-unity-editor-tool":
      description: "创建Unity编辑器工具（含桌面配置界面和后端服务）"
      steps:
        - name: "设计工具架构"
          agent: "unity.csharp.architecture-designer"
          task: "设计编辑器工具架构"
        - name: "实现编辑器扩展"
          agent: "unity.csharp.code-generator"
          task: "实现Editor Window"
        - name: "创建桌面配置工具"
          agent: "desktop.csharp.wpf.code-generator"
          task: "实现配置界面"
        - name: "搭建后端服务"
          agent: "nodejs.express.code-generator"
          task: "实现数据同步API"

  persona: |
    你是一位Unity开发工具链专家。
    你精通编辑器扩展、桌面工具和后端服务的整合。
    你擅长构建完整的游戏开发工具生态。
---
