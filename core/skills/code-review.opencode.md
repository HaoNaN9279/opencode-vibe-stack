---
name: "code-review"
description: "代码审查，检查代码质量、安全性和性能问题"
triggers:
  - "审查这段代码"
  - "代码Review"
  - "检查代码质量"
vibe: "quality-first"

steps:
  - name: "overview"
    prompt: "概述代码的整体结构和功能"
  - name: "security"
    prompt: "检查安全漏洞和敏感信息泄露"
  - name: "performance"
    prompt: "检查性能瓶颈和优化机会"
  - name: "maintainability"
    prompt: "检查代码可维护性和规范性"
  - name: "summary"
    prompt: "汇总问题清单和改进建议"
---
