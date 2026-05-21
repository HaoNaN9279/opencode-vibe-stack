# Blender Python API 编码规范

- 所有插件必须包含 bl_info 元数据
- 使用 bpy.types 注册所有类和属性
- 提供 register / unregister 函数
- 使用 bpy.props 定义可序列化属性
- 尽量使用 layout.operator 而非手动调用
- 使用 context 参数传递数据而非全局变量
- 使用 enumerate 而不是 range(len()) 遍历集合
- Blender 4.0+ 使用新 bpy.types API
