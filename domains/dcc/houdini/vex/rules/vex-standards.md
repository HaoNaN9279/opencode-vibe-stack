# Houdini VEX 编码规范

- 使用 @attr 语法读写属性
- 尽量使用向量运算代替循环
- 避免在循环内创建数组
- 使用 fit() 和 clamp() 规范化数值
- 使用 setattrib() 批量写入属性
- 优先使用 point / prim 函数族
