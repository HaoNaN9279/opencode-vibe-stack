---
name: "debugging"
description: "系统化调试，定位并修复问题"
triggers:
  - "调试这个错误"
  - "修复这个bug"
  - "这个代码为什么出错了"
vibe: "systematic-debug"

steps:
  - name: "reproduce"
    prompt: "分析错误信息，确定复现步骤"
  - name: "isolate"
    prompt: "定位问题所在的模块和代码行"
  - name: "root-cause"
    prompt: "分析根本原因"
  - name: "fix"
    prompt: "提供修复方案"
  - name: "verify"
    prompt: "验证修复是否正确"
---
