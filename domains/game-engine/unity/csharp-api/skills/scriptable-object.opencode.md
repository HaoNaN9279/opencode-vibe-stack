---
name: "unity.csharp.scriptable-object"
description: "创建符合最佳实践的Unity ScriptableObject"
triggers:
  - "创建一个ScriptableObject"
  - "用SO存储配置"
  - "SO数据管理"
vibe: "unity-best-practices"
dependencies:
  - "core.skills.csharp-class"
---

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
