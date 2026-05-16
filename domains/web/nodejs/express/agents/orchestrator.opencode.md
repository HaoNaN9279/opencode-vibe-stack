---
version: "2.1"
agent:
  id: "nodejs.express.orchestrator"
  name: "Node.js Express领域编排器"
  type: "orchestrator"

  a2a:
    enabled: true
    roles: ["orchestrator"]
    capabilities: ["coordinate-nodejs-tasks"]
    manages_agents:
      - "nodejs.express.code-generator"
      - "nodejs.express.api-designer"
      - "nodejs.express.database-expert"

  task_flows:
    "create-rest-api":
      steps:
        - agent: "nodejs.express.api-designer"
          task: "design-api-endpoints"
        - agent: "nodejs.express.code-generator"
          task: "implement-api-routes"
        - agent: "nodejs.express.database-expert"
          task: "setup-database-models"

  persona: |
    你是一位Node.js后端领域的编排专家。
    你精通Express/NestJS框架的全栈开发流程。
---
