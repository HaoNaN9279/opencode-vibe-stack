# Unity 游戏引擎开发规则

适用于 AI 辅助 Unity C# 开发的规则。在每个 Unity 项目中遵守。

## 项目结构

- 遵循 Unity 推荐的布局：`Assets/Scripts/`、`Assets/Prefabs/`、`Assets/Scenes/`、`Assets/Resources/`、`Assets/Editor/`。
- 将第三方资源放在 `Assets/Plugins/` 下，绝不直接修改。
- 为每个逻辑模块使用程序集定义文件（`.asmdef`）以强制依赖边界并减少重新编译时间。
- 保持场景数量较少；优先使用附加场景加载和基于 Prefab 的组合，而非单体场景。

## C# 编码规范

- 在项目 Unity 版本支持的范围内使用 C# 9.0+ 特性（target-typed new、records 数据类型、模式匹配）。
- 默认使用 `private`；仅在需要检视面板可见性时用 `[SerializeField]` 暴露字段 —— 绝不使用 `public` 字段进行序列化。
- 使用 `[RequireComponent]` 文档化强制组件依赖。
- 在生产代码中避免 `GameObject.Find()` 和 `FindObjectOfType<>()`；优先使用序列化引用或通过 `[SerializeField]` 进行依赖注入。
- 使用 `Awake()` 进行自初始化，`Start()` 进行跨对象连接，`OnEnable()`/`OnDisable()` 进行订阅管理。
- 始终将 `OnEnable` 订阅与 `OnDisable` 取消订阅配对，以防止委托泄漏。
- 使用 `[AddComponentMenu("")]` 标记不应出现在 AddComponent 菜单中的类。

## API 使用模式

- 仅在绝对必要时使用 `[RuntimeInitializeOnLoadMethod]`；优先从启动场景进行显式初始化。
- 利用 `ScriptableObject` 实现共享配置、事件通道和数据驱动设计 —— 不仅仅是设置。
- 使用 `async/await` 配合 `UniTask`（或 Unity 2023.2+ 的 `Awaitable`）替代协程进行异步操作。
- 对于简单的顺序动画可以使用协程；涉及分支逻辑的任何情况，使用 async。
- 对于运行时生成的对象，优先使用 `ObjectPool<T>` 而非 `Instantiate`/`Destroy`。
- 使用 `Addressables` 或 `AssetBundles` 进行运行时资源加载；在生产中绝不使用 `Resources.Load()`。

## 性能

- 尽可能避免 `Update()`；使用事件、带 `WaitForSeconds` 的 `Coroutine` 或响应式模式。
- 在 `Awake()` 或 `OnEnable()` 中缓存 `GetComponent<T>()` 结果 —— 绝不在 `Update()` 中调用。
- 在编辑时已知引用的情况下，使用 `[SerializeField]` 引用替代运行时 `GetComponent` 查找。
- 避免重复调用 `Camera.main`；在第一个有效帧后缓存引用。
- 在优化前使用 Deep Profiler 进行分析；没有分析数据绝不进行微优化。
- 对频繁生成/销毁的对象（弹丸、粒子、敌人）使用对象池。
- 在旧版 Mono 运行时的热路径中避免 `foreach`；在 `Update()` 中遍历集合时使用 `for` 配合缓存的 `.Count`。

## 常见陷阱

- 绝不在 MonoBehaviour 上调用 `Destroy(this)`；使用 `Destroy(gameObject)` 或 `Destroy(GetComponent<T>())`。
- `OnDestroy()` 在非激活 GameObject 上或应用程序退出时不会被调用；不要依赖它进行关键清理。
- `[ExecuteAlways]` 脚本在编辑模式、编辑时和播放模式下都会运行 —— 始终用 `Application.isPlaying` 检查保护编辑时逻辑。
- Unity 序列化支持 `List<T>` 和数组，但不直接支持 `Dictionary<TKey, TValue>`；使用 `ISerializationCallbackReceiver` 或包装类。
- 不要在 `OnValidate()` 中运行耗时操作；它在每次检视面板更改时都会执行，包括撤销/重做。
- 为 IL2CPP 构建需要 AOT 安全的代码模式；避免 `dynamic`、带有值类型的 `MakeGenericType` 以及大量反射。

## 测试

- 使用 Unity Test Framework 的 Play Mode 和 Edit Mode 测试程序集。
- 将测试文件组织到 `Assets/Tests/EditMode/` 和 `Assets/Tests/PlayMode/` 下。
- 使用从具体组件提取的接口来 Mock `MonoBehaviour` 依赖。
- 对于跨多帧的测试，使用返回类型为 `IEnumerator` 的 `[UnityTest]`。
- 保持 Edit Mode 测试快速（不加载场景）；将 Play Mode 测试用于集成和场景级行为。

## 编辑器工具

- 将仅编辑器脚本放在 `Editor/` 文件夹或仅编辑器程序集定义下。
- 使用 `[CustomEditor]`、`[PropertyDrawer]` 和 `[MenuItem]` 属性扩展编辑器。
- 使用 `EditorGUILayout` 和 `SerializedProperty` 进行检视面板自定义 —— 绝不通过 `target` 直接修改序列化对象。
- 将长时间运行的编辑器操作包装在 `EditorApplication.delayCall` 或 `EditorCoroutine` 中，以保持编辑器响应。
