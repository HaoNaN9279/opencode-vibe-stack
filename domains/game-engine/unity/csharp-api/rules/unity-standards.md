# Unity C# 编码规范

- 避免在 Update 中创建新对象（减少 GC 压力）
- 使用对象池管理频繁创建销毁的对象
- 用 TryGetComponent 代替 GetComponent 判空
- 缓存 GetComponent 引用
- 使用 Input System 包替代旧的 Input Manager
- 使用 Addressables 管理资源加载
- 优先使用 Data-Oriented 设计（ECS）处理大量实体
- 使用 SerializeReference 替代 ScriptableObject 的多态需求
