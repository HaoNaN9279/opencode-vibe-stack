---
name: object-pool
description: 实现 Unity 泛型对象池模式，减少 GC 分配并提升运行时性能
license: MIT
compatibility: opencode
metadata:
  domain: game-engine.unity.csharp-api
---

## What I do

生成基于泛型的 Unity 对象池实现模板，支持预分配、获取、归还操作，减少 Instantiate/Destroy 带来的 GC 压力。

## When to use me

当需要频繁创建和销毁相同类型的 GameObject（如子弹、特效、敌人）时使用。

## Template

```csharp
using UnityEngine;
using System.Collections.Generic;

public class ObjectPool<T> where T : Component
{
    private readonly T _prefab;
    private readonly Queue<T> _pool = new();
    private readonly Transform _parent;

    public ObjectPool(T prefab, int initialSize, Transform parent = null)
    {
        _prefab = prefab;
        _parent = parent;
        for (int i = 0; i < initialSize; i++)
        {
            var obj = Create();
            obj.gameObject.SetActive(false);
            _pool.Enqueue(obj);
        }
    }

    public T Get()
    {
        if (_pool.Count == 0) return Create();
        var obj = _pool.Dequeue();
        obj.gameObject.SetActive(true);
        return obj;
    }

    public void Return(T obj)
    {
        obj.gameObject.SetActive(false);
        _pool.Enqueue(obj);
    }

    private T Create() => Object.Instantiate(_prefab, _parent);
}
```
