# opencode-vibe-stack

这是一个用于管理 OpenCode + OhMyOpenAgent (OMO) AI 智能体配置的**配置管理仓库**。它不包含应用程序代码。

## 这里有什么

- `core/` — 始终加载的常驻配置（规则、技能、智能体、MCP、命令、工具）
- `domains/` — 按类别组织的领域特定配置（`ai/`、`dcc/`、`game-dev/`）
- `stacks/` — 预设的领域组合（`dcc.json`、`game-dev.json`、`ai-training.json` 等）
- `bin/` — CLI 工具（`vibe-stack`）和安装程序

## 配置如何加载

- core目录下的各个文件夹将分别链接到用户配置目录下：~/.config/opencode/
- domain中各个领域的文件夹，将在项目激活该domain后，链接到项目配置目录下：.opencode/

## 在此仓库上工作时

- 领域配置应只包含规则/技能/智能体/MCP 内容——绝不包含模型参数
- 模型配置（提供商、温度等）属于 `~/.config/opencode/oh-my-openagent.jsonc`，不在本仓库范围内
- 所有领域目录遵循相同的结构：`{rules,agents,commands,mcp,skills,tools}/`
- 使用 `vibe-stack` 在项目中测试领域配置（`vibe-stack` 的使用方法见 `vibe-stack help`）
- 当遇到需要查询opencode和oh-myopenagent（oh-my-opencode）插件的功能和API时，通过以下github地址查找其源码：
    - opencode源码地址：https://github.com/anomalyco/opencode
    - oh-my-openagent（oh-my-opencode）源码地址：https://github.com/code-yeongyu/oh-my-openagent
