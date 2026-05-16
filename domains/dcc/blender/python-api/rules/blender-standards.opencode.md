---
version: "2.1"
rules:
  blender_standards:
    - "所有插件必须包含bl_info元数据"
    - "使用bpy.types注册所有类和属性"
    - "提供register/unregister函数"
    - "使用bpy.props定义可序列化属性"
    - "尽量使用layout.operator而非手动调用"
    - "使用context参数传递数据而非全局变量"
    - "使用enumerate而不是range(len())遍历集合"
    - "Blender 4.0+使用新bpy.types API"
---
