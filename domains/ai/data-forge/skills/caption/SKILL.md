---
name: caption
description: 通过 ai_data-forge_caption 工具管理 caption 文件，支持 CRUD、搜索替换（含正则）、重命名、去重、JSON/CSV 导入导出和统计分析。
---

# Caption

管理 `.txt` caption 文件。所有操作均通过 `ai_data-forge_caption` 工具完成。

此工具通过 `uv run python -m data_forge.caption <subcommand>` 调用 DataForge 的 Python 模块。

## ⚠️ 前置检查

确保 DataForge 子模块已初始化：
```
git submodule update --init --depth 1
```

如果遇到依赖问题，在 `libs/data-forge/` 目录下执行 `uv sync`。

## 工具调用

使用 `ai_data-forge_caption` 工具，传入 `subcommand` 参数指定操作类型，其余参数按 snake_case 格式传入。

### `list` — 列出所有 caption 文件

| 参数 | 说明 |
|------|------|
| `directory` | 目标目录，默认 `.` |

```
subcommand: "list"
directory: "./captions"
```

### `create` — 创建 caption

| 参数 | 说明 |
|------|------|
| `file` | (必填) 文件名 |
| `content` | 文件内容（与 content_file 二选一） |
| `content_file` | 从文件读取内容（与 content 二选一） |
| `overwrite` | 覆盖已存在的文件 |

```
subcommand: "create"
file: "img01.txt"
content: "a cat"
```

### `read` — 读取 caption

| 参数 | 说明 |
|------|------|
| `file` | (必填) 文件名 |

```
subcommand: "read"
file: "img01.txt"
```

### `edit` — 编辑 caption

| 参数 | 说明 |
|------|------|
| `file` | (必填) 文件名 |
| `content` | (必填) 新内容 |
| `mode` | update/append/prepend，默认 update |
| `separator` | append/prepend 时的分隔符，默认空格 |

*注意：edit 子命令使用 `--dir` 而非 `--directory`，工具内部会自动转换。*

```
subcommand: "edit"
file: "img01.txt"
content: "new text"
```

```
subcommand: "edit"
file: "img01.txt"
content: ", hi"
mode: "append"
separator: ""
```

### `delete` — 删除 caption

| 参数 | 说明 |
|------|------|
| `file` | 指定文件名（与 pattern/all 三选一） |
| `pattern` | 通配符模式（与 file/all 三选一） |
| `all` | 删除所有（与 file/pattern 三选一） |
| `regex` | pattern 使用正则表达式 |

```
subcommand: "delete"
file: "img01.txt"
```

```
subcommand: "delete"
pattern: "temp_*"
```

### `search` — 搜索 caption

| 参数 | 说明 |
|------|------|
| `query` | (必填) 搜索词 |
| `case_sensitive` | 区分大小写 |
| `regex` | 使用正则搜索 |
| `by_filename` | 按文件名搜索 |

```
subcommand: "search"
query: "cat"
```

### `replace` — 跨文件搜索替换

| 参数 | 说明 |
|------|------|
| `old` | (必填) 被替换的文本 |
| `new` | (必填) 替换后的文本 |
| `case_sensitive` | 区分大小写 |
| `regex` | 使用正则替换 |

```
subcommand: "replace"
old: "cat"
new: "kitten"
```

### `rename` — 重命名

| 参数 | 说明 |
|------|------|
| `old_name` | (必填) 原文件名 |
| `new_name` | (必填) 新文件名 |

```
subcommand: "rename"
old_name: "img01.txt"
new_name: "photo01.txt"
```

### `stats` — 统计/词频

| 参数 | 说明 |
|------|------|
| `word_frequency` | 显示词频 |
| `top_n` | 词频排名前 N，默认 20 |

```
subcommand: "stats"
word_frequency: true
top_n: 50
```

### `export` — 导出 JSON/CSV

| 参数 | 说明 |
|------|------|
| `output` | (必填) 输出文件路径 |
| `format` | json/csv，默认 json |

```
subcommand: "export"
output: "captions.json"
```

### `import` — 导入 JSON/CSV

| 参数 | 说明 |
|------|------|
| `input` | (必填) 输入文件路径 |
| `format` | json/csv，默认 json |
| `overwrite` | 覆盖已存在的文件 |

```
subcommand: "import"
input: "captions.json"
```

### `deduplicate` — 去重

| 参数 | 说明 |
|------|------|
| `keep` | first/last，默认 first |

```
subcommand: "deduplicate"
```
