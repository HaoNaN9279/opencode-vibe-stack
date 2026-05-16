---
version: "2.1"
rules:
  unity_standards:
    - "避免在Update中创建新对象（GC压力）"
    - "使用对象池管理频繁创建销毁的对象"
    - "用TryGetComponent代替GetComponent判空"
    - "缓存GetComponent引用"
    - "使用InputSystem包替代旧的Input Manager"
    - "使用Addressables管理资源加载"
    - "优先使用Data-Oriented设计（ECS）处理大量实体"
    - "使用SerializeReference替代ScriptableObject的多态需求"
---
