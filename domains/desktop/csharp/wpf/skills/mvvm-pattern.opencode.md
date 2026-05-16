---
name: "desktop.csharp.wpf.mvvm-pattern"
description: "WPF MVVM模式实现模板"
triggers:
  - "创建MVVM实现"
  - "WPF ViewModel"
  - "数据绑定模式"
vibe: "clean-architecture"
---

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
