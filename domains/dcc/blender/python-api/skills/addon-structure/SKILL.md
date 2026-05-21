---
name: addon-structure
description: 创建符合规范的 Blender Python 插件基础结构，包含 Operator、Panel 和 register/unregister
license: MIT
compatibility: opencode
metadata:
  domain: dcc.blender.python-api
---

## What I do

生成完整的 Blender Python 插件模板，包括 bl_info 元数据、Operator 类、Panel 类和标准的 register/unregister 函数。

## When to use me

当需要创建新的 Blender 插件时使用 — 无论是简单工具还是复杂扩展的起点。

## Template

```python
bl_info = {
    "name": "{AddonName}",
    "author": "{Author}",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > {TabName}",
    "description": "{Description}",
    "category": "{Category}",
}

import bpy

class {OperatorName}(bpy.types.Operator):
    bl_idname = "{operator_id}"
    bl_label = "{Label}"
    bl_options = {{'REGISTER', 'UNDO'}}

    def execute(self, context):
        return {{'FINISHED'}}

class {PanelName}(bpy.types.Panel):
    bl_label = "{Label}"
    bl_idname = "{panel_id}"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "{TabName}"

    def draw(self, context):
        layout = self.layout
        layout.operator("{operator_id}")

def register():
    bpy.utils.register_class({OperatorName})
    bpy.utils.register_class({PanelName})

def unregister():
    bpy.utils.unregister_class({PanelName})
    bpy.utils.unregister_class({OperatorName})
```
