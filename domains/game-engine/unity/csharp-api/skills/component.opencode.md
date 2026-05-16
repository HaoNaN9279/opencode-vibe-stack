---
name: "unity.csharp.component"
description: "创建Unity MonoBehavior组件"
triggers:
  - "创建一个组件"
  - "写一个MonoBehavior"
  - "创建Unity脚本"
vibe: "unity-best-practices"
---

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
