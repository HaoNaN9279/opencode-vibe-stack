# Unity Game Engine Development Rules

Rules for AI-assisted Unity development with C#. Follow these in every Unity project.

## Project Structure

- Follow Unity's recommended layout: `Assets/Scripts/`, `Assets/Prefabs/`, `Assets/Scenes/`, `Assets/Resources/`, `Assets/Editor/`.
- Place third-party assets under `Assets/Plugins/` and never modify them directly.
- Use assembly definition files (`.asmdef`) for every logical module to enforce dependency boundaries and reduce recompile time.
- Keep scene count low; prefer additive scene loading and prefab-based composition over monolithic scenes.

## C# Coding Conventions

- Use C# 9.0+ features where supported by the project's Unity version (target-typed new, records for data types, pattern matching).
- Prefer `private` by default; only expose fields with `[SerializeField]` when inspector visibility is needed — never use `public` fields for serialization.
- Use `[RequireComponent]` to document mandatory component dependencies.
- Avoid `GameObject.Find()` and `FindObjectOfType<>()` in production code; prefer serialized references or dependency injection via `[SerializeField]`.
- Use `Awake()` for self-initialization, `Start()` for cross-object wiring, and `OnEnable()`/`OnDisable()` for subscription management.
- Always pair `OnEnable` subscriptions with `OnDisable` unsubscriptions to prevent leaked delegates.
- Mark classes that should not appear in the AddComponent menu with `[AddComponentMenu("")]`.

## API Usage Patterns

- Use `[RuntimeInitializeOnLoadMethod]` only when absolutely necessary; prefer explicit initialization from a bootstrap scene.
- Leverage `ScriptableObject` for shared configuration, event channels, and data-driven design — not just settings.
- Use `async/await` with `UniTask` (or Unity 2023.2+ `Awaitable`) instead of coroutines for asynchronous operations.
- Coroutines are acceptable for simple sequenced animations; for anything involving branching logic, use async.
- Prefer `ObjectPool<T>` over `Instantiate`/`Destroy` for runtime-spawned objects.
- Use `Addressables` or `AssetBundles` for runtime asset loading; never use `Resources.Load()` in production.

## Performance

- Avoid `Update()` when possible; use events, `Coroutine` with `WaitForSeconds`, or reactive patterns.
- Cache `GetComponent<T>()` results in `Awake()` or `OnEnable()` — never call it in `Update()`.
- Use `[SerializeField]` references instead of runtime `GetComponent` lookups whenever the reference is known at edit time.
- Avoid `Camera.main` repeatedly; cache the reference after the first valid frame.
- Profile with the Deep Profiler before optimizing; never micro-optimize without profiling data.
- Use object pooling for frequently spawned/destroyed objects (projectiles, particles, enemies).
- Avoid `foreach` in hot paths on older Mono runtimes; use `for` with cached `.Count` when iterating collections in `Update()`.

## Common Pitfalls

- Never call `Destroy(this)` on a MonoBehaviour; use `Destroy(gameObject)` or `Destroy(GetComponent<T>())`.
- `OnDestroy()` is not called on inactive GameObjects or when the application quits; do not rely on it for critical cleanup.
- `[ExecuteAlways]` scripts run in edit mode, edit-time, and play mode — always guard edit-time logic with `Application.isPlaying` checks.
- Unity serialization supports `List<T>` and arrays but not `Dictionary<TKey, TValue>` directly; use `ISerializationCallbackReceiver` or wrapper classes.
- Do not run expensive operations in `OnValidate()`; it executes on every inspector change including undo/redo.
- Building for IL2CPP requires AOT-safe code patterns; avoid `dynamic`, `MakeGenericType` with value types, and heavy reflection.

## Testing

- Use the Unity Test Framework with Play Mode and Edit Mode test assemblies.
- Structure tests under `Assets/Tests/EditMode/` and `Assets/Tests/PlayMode/`.
- Mock `MonoBehaviour` dependencies using interfaces extracted from the concrete components.
- Use `[UnityTest]` with `IEnumerator` return type for tests that span multiple frames.
- Keep Edit Mode tests fast (no scene loading); use Play Mode tests for integration and scene-level behaviour.

## Editor Tooling

- Place editor-only scripts under an `Editor/` folder or an Editor-only assembly definition.
- Extend the editor with `[CustomEditor]`, `[PropertyDrawer]`, and `[MenuItem]` attributes.
- Use `EditorGUILayout` and `SerializedProperty` for inspector customizations — never modify serialized objects through `target` directly.
- Wrap long-running editor operations in `EditorApplication.delayCall` or `EditorCoroutine` to keep the editor responsive.
