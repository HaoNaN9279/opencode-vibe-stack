---
version: "2.1"
agent:
  id: "houdini.hdk.orchestrator"
  name: "Houdini HDK领域编排器"
  type: "orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-houdini-hdk-tasks"]
    manages_agents:
      - "houdini.hdk.code-generator"
      - "houdini.hdk.architecture-designer"

  task_flows:
    "create-hdk-plugin":
      steps:
        - agent: "houdini.hdk.architecture-designer"
          task: "design-plugin-architecture"
        - agent: "houdini.hdk.code-generator"
          task: "implement-plugin-code"

  persona: |
    你是一位Houdini HDK领域的编排专家。
    你熟悉HDK插件开发的完整流程。
---
