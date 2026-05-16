---
name: "unity.csharp.monobehaviour"
description: "Unity MonoBehavior生命周期和事件函数使用指南"
triggers:
  - "MonoBehavior生命周期"
  - "Unity事件函数"
  - "脚本执行顺序"
vibe: "unity-best-practices"
---

```csharp
public class {Name} : MonoBehaviour
{
    // 生命周期顺序:
    // Awake -> OnEnable -> Start -> Update -> LateUpdate -> OnDisable -> OnDestroy

    private void Awake()   // 只调用一次，即使脚本未启用
    private void OnEnable() // 每次启用时调用
    private void Start()    // 第一次Update之前调用
    private void FixedUpdate() // 固定时间间隔调用（物理更新）
    private void Update()   // 每帧调用
    private void LateUpdate() // Update之后调用
    private void OnDisable() // 每次禁用时调用
    private void OnDestroy() // 销毁时调用
}
```
