---
name: component
description: 创建符合 Unity 最佳实践的 MonoBehaviour 组件，包含标准生命周期方法和序列化字段声明
license: MIT
compatibility: opencode
metadata:
  domain: game-engine.unity.csharp-api
---

## What I do

生成标准的 Unity MonoBehaviour 组件模板，包含 Awake/Start/Update 等生命周期方法、序列化字段声明和 Header attribute 组织的参数分组。

## When to use me

当需要在 Unity 项目中创建新的 C# 脚本组件时使用。

## Template

```csharp
using UnityEngine;

public class {Name} : MonoBehaviour
{
    [Header("Dependencies")]
    [SerializeField] private {Type} _{field};

    private void Awake()
    {
        // 初始化引用
    }

    private void Start()
    {
        // 初始化状态
    }

    private void Update()
    {
        // 每帧逻辑
    }
}
```
