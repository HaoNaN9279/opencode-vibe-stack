---
name: point-wrangle
description: 创建 Houdini Point Wrangle 节点的 VEX 代码模板，操作所有点属性
license: MIT
compatibility: opencode
metadata:
  domain: dcc.houdini.vex
---

## What I do

生成 Houdini Point Wrangle 的 VEX 模板，提供点索引访问、点数量查询的基础结构，运行于所有点上。

## When to use me

当需要在 Houdini 中创建点层级操作的 VEX 代码时使用 — 如位置偏移、属性计算、点选择等。

## Template

```vex
// Point Wrangle: {Description}
// Run Over: Points

int point = @ptnum;
int numPoints = npoints(0);

// 你的代码在这里
```
