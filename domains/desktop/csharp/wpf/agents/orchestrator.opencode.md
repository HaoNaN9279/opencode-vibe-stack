---
version: "2.1"
agent:
  id: "desktop.csharp.wpf.orchestrator"
  name: "C# WPF领域编排器"
  type: "orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-wpf-tasks"]
    manages_agents:
      - "desktop.csharp.wpf.ui-designer"
      - "desktop.csharp.wpf.code-generator"

  task_flows:
    "create-wpf-application":
      steps:
        - agent: "desktop.csharp.wpf.ui-designer"
          task: "design-main-window-layout"
        - agent: "desktop.csharp.wpf.code-generator"
          task: "implement-viewmodel-code"
        - agent: "desktop.csharp.wpf.ui-designer"
          task: "polish-ui-controls"

  persona: |
    你是一位C# WPF桌面应用开发编排专家。
    你熟悉MVVM架构和WPF完整的开发流程。
---
