---
name: unity
description: 当用户需要处理 Unity 游戏引擎开发相关任务时使用。包括 C# 脚本编写、编辑器工具开发、场景搭建、性能优化、资源管线管理、构建部署等全流程 Unity 开发工作。同时提供通过 MCP 工具与 Unity Editor 进行实时交互的能力。
license: MIT
compatibility: opencode
metadata:
  audience: developers
  category: game-development
  domain: game-dev/unity
---

# Unity 游戏开发技能

通用 Unity 开发技能，涵盖 C# 编码规范、编辑器扩展、资源管线、性能优化、测试调试等核心环节。同时集成 MCP（Model Context Protocol）工具链，实现 AI 与 Unity Editor 的实时双向通信。

加载此技能后，AI 将遵循以下统一的工作流和规范处理 Unity 相关的开发任务。

---

## MCP 工具集成

本技能通过 MCP 工具链与 Unity Editor 直接交互。当前可用及预留的 MCP 工具如下：

### 当前可用

#### hn_unity_mcp
与 Unity Editor 实时交互的 MCP 桥接工具。通过 HTTP 与 Unity 编辑器内的 McpService 通信，支持读取编辑器状态、执行命令等操作。

**前置条件**：
1. Unity Editor 已打开并加载了目标项目
2. Unity 项目中已导入 `HNUnityMCP` 编辑器扩展（位于 `Assets/Editor/HNUnityMCP/`）
3. Python 侧的 `hn-unity-mcp` MCP Server 已启动（通过 `hn-unity-mcp` 命令）
4. Windows 上首次使用时需以管理员身份执行端口注册：`netsh http add urlacl url=http://+:18080/ user=Everyone`

**可用工具**：
- `get_compile_errors` — 获取 Unity 控制台中的编译错误和警告信息

### 预留扩展位

> 以下 MCP 工具位已预留，待后续扩展：
>
> - **`list_scenes`** — 列出项目中所有场景
> - **`open_scene`** — 在编辑器中打开指定场景
> - **`get_game_objects`** — 获取当前场景中的 GameObject 层级结构
> - **`execute_menu`** — 执行 Unity 编辑器菜单命令
> - **`run_editmode_tests`** — 运行 Edit Mode 测试
> - **`run_playmode_tests`** — 运行 Play Mode 测试
> - **`get_console_log`** — 获取编辑器控制台日志
> - **`set_prefab`** — 修改 Prefab 属性
> - **`execute_unity_command`** — 执行自定义 Unity 编辑器命令

---

## 使用时机

本技能在以下场景中应被加载使用：

- 用户描述了一个 Unity 项目或功能需求，需要编写 C# 脚本
- 需要修改 Unity 场景中的 GameObject、组件或 Prefab
- 需要排查 Unity 编译错误、运行时异常或性能问题
- 需要创建或扩展 Unity 编辑器工具（Inspector、Editor Window、MenuItem）
- 需要配置资源管线（Addressables、AssetBundles、Resources）
- 需要进行 Unity 项目构建、平台部署或 CI/CD 配置
- 需要与 Unity Editor 实时交互（读取编译状态、执行命令等）

---

## 核心工作流

### 1. 需求分析与规划

- 明确目标 Unity 版本和渲染管线（URP / HDRP / Built-in）
- 确认目标平台（Windows / macOS / Linux / Android / iOS / Console）
- 识别依赖关系（第三方插件、Package Manager 包）
- 利用 `get_compile_errors` 检查当前项目编译状态，确保从干净状态开始

### 2. 项目结构与代码组织

遵循 Unity 项目布局标准，详见领域规则 `unity.md`：

- `Assets/Scripts/` — C# 脚本
- `Assets/Prefabs/` — 预制体
- `Assets/Scenes/` — 场景文件
- `Assets/Resources/` — Resources 加载的资源（尽量少用，优先 Addressables）
- `Assets/Editor/` — 编辑器扩展代码
- `Assets/Plugins/` — 第三方插件（绝不直接修改）
- 为每个逻辑模块创建程序集定义文件（`.asmdef`）

### 3. 编码规范

#### MonoBehaviour 生命周期管理

```csharp
public class PlayerController : MonoBehaviour
{
    [SerializeField] private float _moveSpeed = 5f;
    private Rigidbody _rb;
    private Animator _animator;

    private void Awake()
    {
        // 自初始化：缓存组件引用，绝不重复 GetComponent
        _rb = GetComponent<Rigidbody>();
        _animator = GetComponent<Animator>();
    }

    private void Start()
    {
        // 跨对象连接：获取其他组件的引用，注册事件
    }

    private void OnEnable()
    {
        // 订阅事件（必须与 OnDisable 配对）
    }

    private void OnDisable()
    {
        // 取消订阅，防止委托泄漏
    }

    private void Update()
    {
        // 尽量避免 Update；使用事件、协程或响应式模式替代
    }
}
```

#### 序列化与 Inspector 规范

- 使用 `[SerializeField] private` 而非 `public` 字段暴露 Inspector
- 使用 `[SerializeField] private` 缓存组件引用，避免运行时 `GetComponent`
- 使用 `[RequireComponent]` 声明强制组件依赖
- 使用 `[AddComponentMenu("")]` 标记不应出现在 AddComponent 菜单中的类
- 使用 `[Range(min, max)]`、`[Min(val)]`、`[Tooltip("")]` 等属性优化 Inspector 体验

#### ScriptableObject 数据驱动

```csharp
// 使用 ScriptableObject 管理游戏配置和数据
[CreateAssetMenu(fileName = "NewItemConfig", menuName = "Game/Item Config")]
public class ItemConfig : ScriptableObject
{
    public string itemName;
    public Sprite icon;
    public int maxStack;
    public GameObject prefab;
}
```

### 4. 编辑器扩展开发

- 编辑器脚本放在 `Editor/` 目录或独立的 Editor 程序集定义下
- 使用 `[CustomEditor]` 自定义 Inspector、`[PropertyDrawer]` 自定义属性绘制
- 使用 `[MenuItem]` 添加编辑器菜单项
- 使用 `EditorGUILayout` 和 `SerializedProperty` 操作序列化属性
- 耗时操作包装在 `EditorApplication.delayCall` 或 `EditorCoroutine` 中

### 5. 资源与资源管线

- 优先使用 **Addressables** 进行运行时资源加载
- 避免使用 `Resources.Load()`（除非有充分理由）
- Prefab 嵌套保持合理深度（不超过 3-4 层）
- 使用 Sprite Atlas 合并 UI 图集
- 纹理压缩格式按平台配置（ASTC for Android, PVRTC for iOS, BC7 for PC）

### 6. 性能优化

- **在优化前必须使用 Profiler（Deep Profile）进行分析**，根据数据决策
- 缓存 `GetComponent<T>()` 结果：在 `Awake()` 中获取，绝不放在 `Update()` 中
- 使用对象池（`ObjectPool<T>`）管理频繁生成/销毁的对象
- 避免 `Camera.main` 重复调用，在 `Start()` 中缓存
- 使用 `CompareTag()` 而非字符串比较
- 热路径中避免 `foreach`（旧版 Mono），使用 `for` 配合缓存的 `.Count`
- 使用 LOD、遮挡剔除（Occlusion Culling）、Level Streaming 优化渲染
- UI 使用 Canvas 合并策略，减少 Draw Call
- 使用 `UnityEngine.Pool`（Unity 2021.3+ 内置）实现对象池

```csharp
using UnityEngine.Pool;

public class BulletPool : MonoBehaviour
{
    [SerializeField] private Bullet _prefab;
    private ObjectPool<Bullet> _pool;

    private void Awake()
    {
        _pool = new ObjectPool<Bullet>(
            createFunc: () => Instantiate(_prefab),
            actionOnGet: (b) => b.gameObject.SetActive(true),
            actionOnRelease: (b) => b.gameObject.SetActive(false),
            actionOnDestroy: (b) => Destroy(b.gameObject),
            collectionCheck: false,
            defaultCapacity: 20
        );
    }

    public Bullet Get() => _pool.Get();
    public void Release(Bullet b) => _pool.Release(b);
}
```

### 7. 异步与协程

- 使用 **UniTask**（或 Unity 2023.2+ 的 `Awaitable`）替代协程进行异步操作
- 简单顺序动画可使用协程；涉及分支逻辑的使用 async/await
- 所有异步操作考虑生命周期管理：与 `CancellationToken` 结合，防止对象销毁后继续执行

### 8. 测试

- 使用 Unity Test Framework（UTF）编写 Edit Mode 和 Play Mode 测试
- Edit Mode 测试放在 `Assets/Tests/EditMode/`，Play Mode 测试放在 `Assets/Tests/PlayMode/`
- Edit Mode 测试保持快速（不加载场景）
- Play Mode 测试用于集成和场景级行为验证
- 跨帧测试使用返回 `IEnumerator` 的 `[UnityTest]`

### 9. 构建与部署

- 构建前先通过 `get_compile_errors` 确认零编译错误
- 按平台配置 Player Settings（图标、包名、分辨率、图形 API）
- 使用 **Addressables** 构建远端资源包
- IL2CPP 构建注意 AOT 安全的代码模式：避免 `dynamic`、值类型的 `MakeGenericType`、大量反射

---

## MCP 工具使用指南

### hn_unity_mcp 使用

当需要在 Unity Editor 中检查状态或执行操作时，通过以下方式调用 MCP 工具：

```
// 通过 skill 工具的 MCP 调用方式
skill_mcp(mcp_name="hn-unity-mcp", tool_name="get_compile_errors")
```

返回结果包含编译错误列表及其摘要统计。

### Unity Editor 未启动处理

如果 MCP 工具调用返回 "Unity MCP 服务未启动" 错误，按照以下步骤排查：

1. 确认 Unity Editor 已打开并加载了目标项目
2. 确认项目中已导入 HNUnityMCP 编辑器扩展
3. 确认 Python 侧的 MCP Server 已启动（`hn-unity-mcp` 命令）
4. 若为首次使用，检查端口 ACL 注册是否完成

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `UNITY_MCP_HOST` | `localhost` | Unity MCP 服务主机地址 |
| `UNITY_MCP_PORT` | `18080` | Unity MCP 服务端口 |

---

## 常见陷阱与注意事项

| 陷阱 | 正确做法 |
|------|---------|
| `Destroy(this)` 在 MonoBehaviour 上 | 使用 `Destroy(gameObject)` |
| 依赖 `OnDestroy()` 进行关键清理 | `OnDestroy()` 在非激活或退出时可能不调用 |
| `[ExecuteAlways]` 未保护编辑时逻辑 | 始终用 `Application.isPlaying` 检查保护 |
| 直接序列化 `Dictionary<TKey, TValue>` | 使用 `ISerializationCallbackReceiver` 或包装类 |
| `OnValidate()` 中执行耗时操作 | `OnValidate()` 每次 Inspector 变更都执行 |
| 使用 `FindObjectOfType<>()` / `GameObject.Find()` | 优先序列化引用或依赖注入 |
| 忽视 IL2CPP 约束编写反射代码 | 避免 `dynamic`、值类型的 `MakeGenericType` |

---

## 参考

- 领域规则文件：`rules/unity.md` — Unity 项目结构规范、C# 编码约定
- 领域规则文件：`rules/data-forge.md` — 数据转换相关约束
- MCP 配置：`mcp/unity.json` — hn_unity_mcp 注册配置
- MCP 源码：`mcp/HNUnityMCP/` — 完整的 MCP 桥接实现
