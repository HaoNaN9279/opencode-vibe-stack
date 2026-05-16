---
name: "code-refactor"
description: "智能代码重构，保持功能不变的同时提升代码质量"
triggers:
  - "重构这段代码"
  - "优化这个函数"
  - "让这段代码更清晰"
vibe: "clean-architecture"

steps:
  - name: "analyze"
    prompt: "分析以下代码的结构、问题和改进点"
  - name: "plan"
    prompt: "给出重构计划，说明每个步骤的目的"
  - name: "execute"
    prompt: "实现重构后的代码，保持功能完全一致"
  - name: "verify"
    prompt: "验证重构后的代码与原代码功能等价"
---
