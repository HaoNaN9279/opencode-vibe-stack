# opencode-vibe-stack

这是一个用于管理 OpenCode + OhMyOpenAgent (OMO) AI 智能体配置的**配置管理仓库**。

项目核心逻辑使用 **Python 3.11+** 编写，通过 **uv** 管理虚拟环境和打包。CLI 入口定义在 `pyproject.toml` 的 `[project.scripts]` 中。

## 这里有什么

- `core/` — 始终加载的常驻配置（规则、技能、智能体、MCP、命令、工具）
- `domains/` — 按类别组织的领域特定配置（`ai/`、`dcc/`、`game-dev/`）
- `stacks/` — 预设的领域组合（`dcc.json`、`game-dev.json`、`ai-training.json` 等）
- `src/vibe_stack/` — Python 核心逻辑包（CLI、MCP 注册、符号链接管理、配置解析）
- `bin/` — 遗留 CLI 包装脚本和安装程序

## 配置如何加载

- core目录下的各个文件夹将分别链接到用户配置目录下：~/.config/opencode/
- domain中各个领域的文件夹，将在项目激活该domain后，链接到项目配置目录下：.opencode/

## MCP 注册机制

vibe-stack 使用**用户级 MCP 注册表**来管理 MCP 服务器可执行文件的路径：

- 注册表文件：`~/.config/opencode/vibe-stack-mcp.jsonc`
- 模板位于：`core/mcp/registry-template.jsonc`
- 用户在注册表中声明 MCP 服务器名称到可执行路径的映射
- 激活领域时，`vibe-stack` 读取注册表，解析 MCP JSON 配置中的占位符，将解析后的条目写入对应的 OpenCode/OMO 配置文件中
- Core MCP 条目写入 `~/.config/opencode/opencode.json`（带 `vibe:core-` 前缀）
- Domain MCP 条目写入 `.opencode/oh-my-openagent.jsonc`（带 `vibe:` 前缀）

这种机制将 MCP 服务器的**声明**（领域 MCP JSON 配置）与**路径解析**（用户本机注册表）分离，避免了在配置中硬编码可执行路径。

## Python 编码规范

本项目遵循以下 Python 编码约定：

- **类型注解** — 所有函数签名必须包含完整的类型注解（使用 `from __future__ import annotations` 启用延迟求值）
- **pathlib** — 所有文件系统路径使用 `pathlib.Path`，不使用 `os.path` 或字符串路径
- **stdlib 优先** — 优先使用 Python 标准库，避免引入不必要的第三方依赖
- **Google 风格 docstring** — 公共函数和类使用 Google 风格的文档字符串（含 Parameters / Returns 节）
- **异常层次** — 自定义异常继承自 `VibeStackError`（位于 `vibe_stack/__init__.py`）
- **常量集中管理** — 路径前缀、文件名等常量定义在 `vibe_stack/constants.py` 中
- **模块职责单一** — 按功能拆分到独立模块（`mcp.py`、`registry.py`、`resolver.py`、`config.py`、`symlinks.py` 等）

## 在此仓库上工作时

- 领域配置应只包含规则/技能/智能体/MCP 内容——绝不包含模型参数
- 模型配置（提供商、温度等）属于 `~/.config/opencode/oh-my-openagent.jsonc`，不在本仓库范围内
- 所有领域目录遵循相同的结构：`{rules,agents,commands,mcp,skills,tools}/`
- 使用 `vibe-stack` 在项目中测试领域配置（`vibe-stack` 的使用方法见 `vibe-stack help`）
- `src/vibe_stack/` 下的 Python 代码修改后可以通过 `uv run vibe-stack` 测试
- 当遇到需要查询opencode和oh-myopenagent（oh-my-opencode）插件的功能和API时，通过以下github地址查找其源码：
    - opencode源码地址：https://github.com/anomalyco/opencode
    - oh-my-openagent（oh-my-opencode）源码地址：https://github.com/code-yeongyu/oh-my-openagent

## OMO Keyword-Detector 模式触发词统计

OMO 的 `keyword-detector` hook 在每次消息被发送时扫描文本，匹配到特定关键词后自动注入对应的模式提示（mode prompt）。以下是所有内置模式及其**中文/英文**触发词统计。

### Ultrawork — 全马力执行模式

| 项目 | 内容 |
|------|------|
| **正则** | `/\b(ultrawork\|ulw)\b/i` |
| **英文** (2) | `ultrawork`, `ulw` |
| **中文** (0) | — |
| **效果** | 注入 ultrawork 模式提示，全并行探索、深度执行，直到任务完成 |

### Search — 搜索/查找模式

| 项目 | 内容 |
|------|------|
| **正则** | `/\b(search\|find\|locate\|lookup\|look\s*up\|explore\|discover\|scan\|grep\|query\|browse\|detect\|trace\|seek\|track\|pinpoint\|hunt)\b\|where\s+is\|show\s+me\|list\s+all\|.../i` |
| **英文** (20) | `search`, `find`, `locate`, `lookup`, `look up`, `explore`, `discover`, `scan`, `grep`, `query`, `browse`, `detect`, `trace`, `seek`, `track`, `pinpoint`, `hunt`, `where is`, `show me`, `list all` |
| **中文** (11) | `搜索`, `查找`, `寻找`, `查询`, `检索`, `定位`, `扫描`, `发现`, `在哪里`, `找出来`, `列出` |
| **效果** | 注入搜索模式提示，聚焦网络搜索和文档查询 |

### Analyze — 深度分析模式

| 项目 | 内容 |
|------|------|
| **正则** | `/\b(analyze\|analyse\|investigate\|examine\|research\|study\|deep[\s-]?dive\|inspect\|audit\|evaluate\|assess\|review\|diagnose\|scrutinize\|dissect\|debug\|comprehend\|interpret\|breakdown\|understand)\b\|why\s+is\|how\s+does\|how\s+to\|.../i` |
| **英文** (23) | `analyze`, `analyse`, `investigate`, `examine`, `research`, `study`, `deep dive` / `deep-dive` / `deepdive`, `inspect`, `audit`, `evaluate`, `assess`, `review`, `diagnose`, `scrutinize`, `dissect`, `debug`, `comprehend`, `interpret`, `breakdown`, `understand`, `why is`, `how does`, `how to` |
| **中文** (12) | `分析`, `调查`, `检查`, `剖析`, `深入`, `诊断`, `解释`, `调试`, `为什么`, `原理`, `搞清楚`, `弄明白` |
| **效果** | 注入 analyze 模式提示，要求先 gather context、并行探索、consult 专家后再行动 |

### Team — 团队模式

| 项目 | 内容 |
|------|------|
| **正则** | `/\bteam[\s_-]?mode\b/i` |
| **英文** (4) | `team mode`, `team-mode`, `team_mode`, `teammode` |
| **中文** (0) | — |
| **效果** | 注入团队模式提示，强制通过 `team_*` 工具协调多智能体并行工作 |

### Hyperplan — 对抗性规划模式

| 项目 | 内容 |
|------|------|
| **正则** | `/\bhyperplan\b\|(?<![\w.])hpp\b/i` |
| **英文** (2) | `hyperplan`, `hpp`（排除 C++ `.hpp` 文件扩展名误触） |
| **中文** (0) | — |
| **效果** | 注入 hyperplan 模式提示，启动 5 个对抗性批评者交叉审查计划 |

### Hyperplan-Ultrawork 组合模式

| 项目 | 内容 |
|------|------|
| **正则** | `/\b(?:hpp\|hyperplan)\s+(?:ulw\|ultrawork)\b\|\b(?:ulw\|ultrawork)\s+(?:hpp\|hyperplan)\b/i` |
| **英文** (8 种组合) | `hpp ulw`, `hpp ultrawork`, `hyperplan ulw`, `hyperplan ultrawork`, `ulw hpp`, `ulw hyperplan`, `ultrawork hpp`, `ultrawork hyperplan` |
| **中文** (0) | — |
| **效果** | 同时注入 hyperplan + ultrawork 模式提示 |

> **注意**：以上仅统计英文和中文触发词。OMO 实际正则中还包含韩文（`분석`, `검색` 等）、日文（`分析`, `検索` 等）、越南文（`phân tích`, `tìm kiếm` 等）等多语言触发词，完整触发词总数约 120+。
>
> **配置**：可通过 `~/.config/opencode/oh-my-openagent.jsonc` 或 `.opencode/oh-my-openagent.jsonc` 中的 `disabled_keywords` 禁用特定模式：
> ```jsonc
> {
>   "keyword_detector": {
>     "disabled_keywords": ["search", "analyze"]
>   }
> }
> ```
