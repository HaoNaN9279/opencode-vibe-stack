---
name: "dcc.houdini.vex.primitive-wrangle"
description: "创建Houdini Primitive Wrangle节点的VEX代码"
triggers:
  - "创建Primitive Wrangle"
  - "写面操作的VEX"
  - "遍历所有面"
vibe: "houdini-vex-optimized"
dependencies:
  - "dcc.houdini.vex.skills.basics"
---

```vex
// Primitive Wrangle: {Description}
// Run Over: Primitives

int prim = @primnum;
int numPrims = nprimitives(0);

// 你的代码在这里
```
