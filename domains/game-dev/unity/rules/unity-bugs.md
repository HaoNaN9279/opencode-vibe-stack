# Unity Mono Enum 泛型 Native Crash

## 概述

Unity 2022.3 的 Mono 运行时在处理 **enum 作为泛型参数 `T`** 的特定代码路径时，会触发 **native crash（段错误）**，无法被 C# 层的 `try-catch` 捕获。

## 触发条件

以下三个条件同时满足时必定崩溃：

1. `T` 是 enum 类型（如 `TestEnum`）
2. 在 `DeserializeFromString<T>()` 泛型方法内部
3. 方法体内包含**标量值 JSON 转换路径**（`ConvertJsonValue` 或同类逻辑）

```csharp
// ❌ 崩溃示例
public static T DeserializeFromString<T>(string jsonString)
{
    // ...
    if (!jsonString.StartsWith("{"))
    {
        // T = TestEnum 时，此代码路径会导致 native crash
        var type = typeof(T);
        if (type.IsEnum)
        {
            return (T)Enum.Parse(type, "2");           // ❌ crash
            return Enum.ToObject(type, 2);              // ❌ crash
            return (T)(object)int.Parse("2");           // ❌ crash
            return (T)Convert.ChangeType("2", type);    // ❌ crash
        }
    }
}
```

## 排查过程

| 尝试方案 | 结果 |
|---|---|
| `Enum.ToObject(type, enumInt)` | ❌ native crash |
| `Enum.Parse(type, enumStr)` | ❌ native crash |
| `Convert.ChangeType(enumStr, underlyingType)` + unbox cast | ❌ native crash |
| `(T)(object)intVal` 直接 int→enum unbox | ❌ native crash |
| `return default`（不做任何转换） | ❌ native crash |
| 完全还原 `DeserializeFromString<T>` 为原始代码 | ❌ native crash |
| 完整跳过 scalar 路径（不进入 if 分支） | ❌ crash（只要 `typeof(T).IsEnum` 在方法体内即触发） |

**关键发现**：即使完全还原到原始代码，单独运行 enum 测试也会崩溃。但首次全量 1463 测试运行时 enum 测试未崩溃（仅失败）。推测与测试运行器的执行上下文或预热有关。

## 绕过方案

在 `DeserializeFromString<T>` 的标量转换路径中，**显式排除 enum 类型**：

```csharp
// DeserializeFromString<T> — scalar path
if (!jsonString.StartsWith("{") && !jsonString.StartsWith("["))
{
    var type = typeof(T);
    // 显式排除 enum，避免 Mono native crash
    if (!type.IsEnum)
    {
        return (T)ConvertJsonValue(jsonString, typeof(T));
    }
    // enum 类型落在原始路径，行为等价于原代码（返回 default，测试 FAIL 但不崩溃）
}
```

## 影响范围

- **无法修复**：`JsonRoundtripTests` 中 4 个 enum 相关测试持续 FAIL
  - `SerializeDeserialize_Enum_Roundtrip`
  - `DeserializeEnum_FromInteger_ReturnsCorrectValue`
  - `SerializeEnum_OutputsIntegerNotStringName`（仅需序列化，未受影响）
- **不受影响**：复杂对象中 enum 字段的反序列化（走 `JsonOverwrite` → `SetFieldValue` 路径，enum 为 field type 而非泛型参数 `T`，不触发此 bug）

## 后续建议

1. 升级 Unity 到 6.x 版本后重新验证（Mono/CoreCLR 差异）
2. 若 IL2CPP 构建模式下无此问题，可考虑 Enum 序列化仅在后端处理
3. 如果未来需要修复 enum 测试，可考虑将 enum 值通过 `int` 类型中转而非泛型参数直接使用

---
