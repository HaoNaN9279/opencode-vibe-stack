---
name: scriptable-object
description: 创建符合最佳实践的 Unity ScriptableObject，用于数据驱动的配置和资源管理
license: MIT
compatibility: opencode
metadata:
  domain: game-engine.unity.csharp-api
---

## What I do

生成标准 Unity ScriptableObject 模板，包含 CreateAssetMenu attribute、分类的 Header、OnEnable 初始化方法。

## When to use me

当需要用 ScriptableObject 存储配置数据、共享游戏数据、或实现数据驱动设计时使用。

## Template

```csharp
using UnityEngine;

[CreateAssetMenu(fileName = "{Name}", menuName = "{MenuPath}")]
public class {Name} : ScriptableObject
{
    [Header("Settings")]
    // public variables here

    [Header("Runtime")]
    // private runtime variables here

    private void OnEnable()
    {
        // 初始化代码
    }
}
```
