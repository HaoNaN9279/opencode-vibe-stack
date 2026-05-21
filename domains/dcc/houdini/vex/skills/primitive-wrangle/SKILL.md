---
name: primitive-wrangle
description: 创建 Houdini Primitive Wrangle 节点的 VEX 代码模板，操作所有面属性
license: MIT
compatibility: opencode
metadata:
  domain: dcc.houdini.vex
---

## What I do

生成 Houdini Primitive Wrangle 的 VEX 模板，提供面索引访问、面数量查询的基础结构，运行于所有面上。

## When to use me

当需要在 Houdini 中创建面层级操作的 VEX 代码时使用 — 如面属性编辑、材质分配、分组等。

## Template

```vex
// Primitive Wrangle: {Description}
// Run Over: Primitives

int prim = @primnum;
int numPrims = nprimitives(0);

// 你的代码在这里
```
