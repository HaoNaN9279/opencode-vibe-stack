---
name: caption
description: 通过 DataForge CLI 管理caption文件，支持 CRUD、搜索替换（含正则）、重命名、去重、JSON/CSV 导入导出和统计分析。
---

# Caption

管理 `.txt` caption文件。所有命令均支持 `--directory` (默认 `.`)。

## ⚠️ 前置检查
```
data-forge --help
```
未安装：`git clone https://github.com/HaoNan9279/DataForge.git && cd DataForge && uv sync`

## 命令

### `caption list` — 列出所有caption文件
```
data-forge caption list --directory ./captions
```

### `caption create` — 创建caption
- `--file` (必填) | `--content` 或 `--content-file` (二选一) | `--overwrite`
```
data-forge caption create --directory ./captions --file img01.txt --content "a cat"
```

### `caption read` — 读取caption
- `--file` (必填)
```
data-forge caption read --directory ./captions --file img01.txt
```

### `caption edit` — 编辑caption
- `--file` `--content` (必填)
- `--mode` update/append/prepend (默认 update) | `--separator` (默认空格)
```
data-forge caption edit --dir ./captions --file img01.txt --content "new text"
data-forge caption edit --dir ./captions --file img01.txt --content ", hi" --mode append --separator ""
```

### `caption delete` — 删除caption
- `--file` 或 `--pattern` 或 `--all` (三选一) | `--regex`
```
data-forge caption delete --directory ./captions --file img01.txt
data-forge caption delete --directory ./captions --pattern "temp_*"
```

### `caption search` — 搜索caption
- `--query` (必填) | `--case-sensitive` | `--regex` | `--by-filename`
```
data-forge caption search --directory ./captions --query "cat"
```

### `caption replace` — 跨文件搜索替换
- `--old` `--new` (必填) | `--case-sensitive` | `--regex`
```
data-forge caption replace --directory ./captions --old "cat" --new "kitten"
```

### `caption rename` — 重命名
- `--old-name` `--new-name` (必填)
```
data-forge caption rename --directory ./captions --old-name img01.txt --new-name photo01.txt
```

### `caption stats` — 统计/词频
- `--word-frequency` 显示词频 | `--top-n` (默认 20)
```
data-forge caption stats --directory ./captions
data-forge caption stats --directory ./captions --word-frequency --top-n 50
```

### `caption export` — 导出 JSON/CSV
- `--output` (必填) | `--format` json/csv (默认 json)
```
data-forge caption export --directory ./captions --output captions.json
```

### `caption import` — 导入 JSON/CSV
- `--input` (必填) | `--format` json/csv (默认 json) | `--overwrite`
```
data-forge caption import --directory ./captions --input captions.json
```

### `caption deduplicate` — 去重
- `--keep` first/last (默认 first)
```
data-forge caption deduplicate --directory ./captions
```
