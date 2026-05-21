---
name: mvvm-pattern
description: 实现 WPF MVVM 模式的基础 ViewModel 模板，包含 INotifyPropertyChanged 和属性变更通知
license: MIT
compatibility: opencode
metadata:
  domain: desktop.csharp.wpf
---

## What I do

生成基于 INotifyPropertyChanged 的 WPF ViewModel 模板，包含 CallerMemberName 优化的属性变更通知机制。

## When to use me

当需要在 WPF 项目中创建新的 ViewModel、实现数据绑定或构建 MVVM 架构时使用。

## Template

```csharp
using System.ComponentModel;
using System.Runtime.CompilerServices;

public class {ViewModelName} : INotifyPropertyChanged
{
    private {Type} _{field};
    public {Type} {Property}
    {
        get => _{field};
        set
        {
            if (Equals(_{field}, value)) return;
            _{field} = value;
            OnPropertyChanged();
        }
    }

    public event PropertyChangedEventHandler PropertyChanged;

    protected void OnPropertyChanged([CallerMemberName] string name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
```
