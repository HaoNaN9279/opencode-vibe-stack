---
version: "2.1"
agent:
  id: "unity.csharp.orchestrator"
  name: "Unity C#领域编排器"
  type: "orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-unity-csharp-tasks"]
    manages_agents:
      - "unity.csharp.code-generator"
      - "unity.csharp.performance-expert"
      - "unity.csharp.architecture-designer"
      - "unity.csharp.bug-fixer"
      - "unity.csharp.code-reviewer"

  task_flows:
    "create-unity-system":
      steps:
        - agent: "unity.csharp.architecture-designer"
          task: "design-system-architecture"
        - agent: "unity.csharp.code-generator"
          task: "generate-code-from-architecture"
        - agent: "unity.csharp.performance-expert"
          task: "optimize-code-performance"
        - agent: "unity.csharp.code-reviewer"
          task: "review-code-quality"
        - agent: "unity.csharp.code-generator"
          task: "apply-code-review-feedback"

  persona: |
    你是一位Unity C#领域的任务编排专家。
    你精通Unity游戏开发的全流程。
    你擅长将复杂的游戏开发任务分解为可执行的子任务。
---
