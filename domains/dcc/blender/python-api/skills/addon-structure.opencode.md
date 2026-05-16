---
name: "dcc.blender.python.addon-structure"
description: "创建Blender插件的基础结构"
triggers:
  - "创建Blender插件"
  - "Blender Addon模板"
  - "新的插件"
vibe: "blender-best-practices"
---

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
