# C# WPF 编码规范

- 使用 MVVM 模式，View 不直接操作 ViewModel 数据
- 使用数据绑定代替代码后置事件
- 使用 Command 模式处理按钮点击
- 使用 IValueConverter 处理类型转换
- 使用 AsyncCommand 处理异步操作
- 优先使用 x:DataType 编译时绑定
- 使用 CommunityToolkit.Mvvm 简化 MVVM 实现
