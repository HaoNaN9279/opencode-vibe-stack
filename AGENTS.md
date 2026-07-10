# opencode-vibe-stack

面向 **OpenCode** 的分层 AI 智能体配置管理工具。Python 3.11+ + uv。

## 架构文档

项目的完整架构设计见 **`项目架构/架构.md`**。开始任何设计或重大修改前，应先阅读该文档。
该文档包含：领域模型、同步引擎、配置合并、MCP 解析、CLI 命令等所有核心模块的详细设计。

## 项目结构

```
opencode-vibe-stack/
├── core/               ← 常驻配置（rules/ agents/ commands/ mcp/ skills/）
├── domains/            ← 领域定义，通过 domain.json 递归发现（任意深度）
├── stacks/             ← 预定义领域组合（game-dev.json 等）
├── tools/              ← 共享工具代码（集中管理，sync 时生成路径索引）
├── src/vibe_stack/     ← Python 核心逻辑
│   ├── errors.py       ← 异常层次（VibeStackError 及其子类）
│   ├── model/          ← 数据模型（DomainConfig, ActivationState, etc.）
│   ├── loader/         ← 配置加载（domain_loader, stack_loader, core_loader）
│   ├── sync/           ← 同步引擎（engine, copier, config_merger, mcp_resolver, state_manager）
│   ├── writer/         ← 配置写入（jsonc_utils, opencode_writer）
│   ├── cli/            ← CLI 层（commands/{activate,deactivate,info,list_status,sync,use_stack}, formatter）
│   └── utils/          ← 工具函数（logging, path_util）
├── tests/
│   ├── unit/           ← 单元测试（按模块组织）
│   └── integration/    ← 集成测试（端到端场景）
└── 项目架构/           ← 架构设计文档
```

## 核心设计原则

1. **仅依赖 OpenCode** — 不依赖 OhMyOpenAgent，配置目标只有 `opencode.json`
2. **文件拷贝** — domain 激活时拷贝文件到 `.opencode/{namespace}/`，`sync` 触发更新
3. **命名空间子目录** — `.opencode/rules/dcc_blender/blender.md`，保持原始文件名
4. **domain.json 发现** — `domains/**/domain.json` 递归扫描，不限制深度
5. **状态文件追踪** — `.vibe-stack-state.json` 记录所有权，停用时精确删除
6. **5 种目录类型** — rules, agents, commands, mcp, skills（tools 内嵌在 skills 中）
7. **工具集中管理** — 所有工具代码在 `tools/` 下统一管理，`sync` 时生成 `vibe-stack-tools.md` 规则文件供 AI 定位，不随领域复制到项目

## Python 编码规范

- **TDD** — RED（测试先行）→ GREEN（最小实现），测试文件命名 `test_*.py`
- **类型注解** — 所有函数签名含完整类型注解，`from __future__ import annotations`
- **pathlib** — 所有文件路径用 `pathlib.Path`，不用 `os.path`
- **stdlib 优先** — 仅用 Python 标准库，零第三方运行时依赖
- **Google 风格 docstring** — 公共函数/类含 Parameters / Returns 节
- **dataclass** — 数据模型用 `@dataclass`，序列化用 `dataclasses.asdict()`
- **异常层次** — 自定义异常继承 `VibeStackError`（`errors.py`）
- **模块职责单一** — 每个模块只做一件事

## 模块速查

| 模块 | 关键函数 | 用途 |
|------|---------|------|
| `loader/domain_loader` | `discover_domains()`, `load_domain()` | 递归发现 + 加载领域 |
| `loader/core_loader` | `load_core()` | 加载 core/ 配置 |
| `loader/stack_loader` | `load_stack()`, `discover_stacks()` | 加载 stack 定义 |
| `sync/engine` | `activate_domain()`, `deactivate_domain()`, `sync()`, `sync_all_active()` | 编排：加载→复制→合并→写入 |
| `sync/copier` | `sync_domain_files()`, `remove_domain_files()`, `sync_core_files()` | 文件拷贝（增量更新） |
| `sync/config_merger` | `merge_instructions()`, `merge_skills_paths()`, `merge_mcp_servers()` | opencode.json 条目合并 |
| `sync/mcp_resolver` | `resolve_mcp_config()` | MCP 占位符解析（env var → config → PATH） |
| `sync/state_manager` | `read_state()`, `write_state()`, `add_domain()`, `remove_domain()` | .vibe-stack-state.json CRUD |
| `writer/jsonc_utils` | `parse_jsonc()`, `strip_jsonc_comments()` | JSONC 解析（含注释剥离） |
| `writer/opencode_writer` | `read_opencode()`, `write_opencode()`, `merge_vibe_entries()` | 唯一读写 opencode.json 的模块 |
| `utils/path_util` | `detect_vibe_home()`, `namespace_from_key()`, `compute_relative_target()` | 路径工具 |
| `utils/logging` | `setup_logging()`, `get_logger()` | 日志配置 |

## 异常层次

```
Exception
└── VibeStackError
    ├── DomainNotFoundError
    ├── DomainAlreadyActiveError
    ├── DomainNotActiveError
    ├── StackNotFoundError
    ├── ConfigMergeError
    ├── MCPResolveError
    ├── StateFileError
    └── SyncError
```

## 测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 仅单元测试
uv run pytest tests/unit/ -v

# 仅集成测试
uv run pytest tests/integration/ -v

# 运行特定模块测试
uv run pytest tests/unit/sync/test_engine.py -v
```

## CLI 命令

```bash
vibe-stack list              # 列出所有领域
vibe-stack status            # 显示激活状态
vibe-stack info <domain>     # 领域详情
vibe-stack activate <d...>   # 激活领域
vibe-stack deactivate <d...> # 停用领域
vibe-stack use-stack <name>  # 使用预设堆栈
vibe-stack sync              # 刷新 Core + 所有激活领域
```

开发时通过 `uv run vibe-stack <command>` 测试 CLI。

## 领域配置规范

- 每个领域必须包含 `domain.json`（含 name, description, version, tags, dependencies）
- 领域目录结构：`{rules,agents,commands,mcp,skills}/`（5 种）
- 技能目录必须包含 `SKILL.md`
- 工具代码内嵌在技能目录的 `tools/` 子目录中
- 绝不包含模型参数（provider, temperature 等）

## 外部参考

- OpenCode 源码：https://github.com/anomalyco/opencode
- OpenCode 配置 Schema：https://opencode.ai/config.json
- uv 文档：https://docs.astral.sh/uv
