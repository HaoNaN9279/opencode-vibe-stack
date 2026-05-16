---
version: "2.1"
agent:
  id: "blender.python.orchestrator"
  name: "Blender Python领域编排器"
  type: "orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-blender-python-tasks"]
    manages_agents:
      - "blender.python.code-generator"
      - "blender.python.addon-developer"

  task_flows:
    "create-blender-addon":
      steps:
        - agent: "blender.python.code-generator"
          task: "generate-addon-structure"
        - agent: "blender.python.addon-developer"
          task: "implement-addon-operators"

  persona: |
    你是一位Blender Python领域的编排专家。
    你熟悉Blender插件开发的完整流程。
---
