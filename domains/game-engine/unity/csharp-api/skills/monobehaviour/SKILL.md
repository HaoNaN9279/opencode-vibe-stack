---
name: monobehaviour
description: Unity MonoBehaviour 生命周期方法的标准调用顺序和使用指南
license: MIT
compatibility: opencode
metadata:
  domain: game-engine.unity.csharp-api
---

## What I do

提供 Unity MonoBehaviour 生命周期方法的标准调用顺序和每个方法的最佳使用场景。

## When to use me

当编写或审查 Unity 脚本时需要确认生命周期方法的正确用法和调用时序。

## Lifecycle Order

```
Awake → OnEnable → Start → FixedUpdate → Update → LateUpdate → OnDisable → OnDestroy
```

## Reference

```csharp
public class {Name} : MonoBehaviour
{
    private void Awake()        { }  // 只调用一次，即使脚本未启用
    private void OnEnable()     { }  // 每次启用时调用
    private void Start()        { }  // 第一次 Update 之前调用
    private void FixedUpdate()  { }  // 固定时间间隔（物理更新）
    private void Update()       { }  // 每帧调用
    private void LateUpdate()   { }  // Update 之后调用
    private void OnDisable()    { }  // 每次禁用时调用
    private void OnDestroy()    { }  // 销毁时调用
}
```
