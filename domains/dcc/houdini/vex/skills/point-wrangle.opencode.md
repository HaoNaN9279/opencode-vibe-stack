---
name: "dcc.houdini.vex.point-wrangle"
description: "创建Houdini Point Wrangle节点的VEX代码"
triggers:
  - "创建Point Wrangle"
  - "写一个点操作的VEX"
  - "遍历所有点"
vibe: "houdini-vex-optimized"
dependencies:
  - "core.skills.loop"
  - "dcc.houdini.vex.skills.basics"
---

```vex
// Point Wrangle: {Description}
// Run Over: Points

int point = @ptnum;
int numPoints = npoints(0);

// 你的代码在这里
```
