# Blender DCC Development Rules

Rules for AI-assisted Blender addon and tool development with Python. Follow these in every Blender scripting project.

## Project Structure

- Place addons under the Blender addons directory (`~/.config/blender/<version>/scripts/addons/`) during development; use symlinks to your source repository.
- Structure addon directories with `__init__.py` as the entry point, containing `bl_info` dict, `register()`, and `unregister()` functions.
- Separate concerns: `operators.py` for `bpy.types.Operator` subclasses, `panels.py` for `bpy.types.Panel`, `properties.py` for `bpy.types.PropertyGroup`, and `utils.py` for shared helpers.
- Keep UI layout logic in dedicated functions; never mix operator execution logic with panel drawing.
- Version addons with semantic versioning in `bl_info["version"]` and include a `bl_info["warning"]` field for pre-release or experimental addons.

## Python Coding Conventions

- Target Blender's bundled Python version (check `bpy.app.version`); aim for compatibility across the last 2 major Blender releases.
- Prefer `bpy.props` for all UI-exposed properties: `StringProperty`, `FloatProperty`, `IntProperty`, `BoolProperty`, `EnumProperty`, `PointerProperty`, `CollectionProperty`.
- Use `Annotation`-based property declarations (class-level `:` syntax) over the older `=` assignment style.
- Always implement `poll()` classmethod on operators to guard against invalid context states; return `False` unless the operator's prerequisites are met.
- Use `@classmethod` for `poll()` and never reference `self` inside it.
- Wrap file I/O operations in try-except blocks and report errors via `self.report({'ERROR'}, message)`.

## API Usage Patterns

- Access scene data through `context.scene` within operators and panels; never use `bpy.context.scene` directly — always use the context parameter.
- Use `bpy.data` for creating/accessing data blocks (`bpy.data.objects.new()`, `bpy.data.meshes.new()`, etc.).
- Prefer `bpy.types` for type references (`bpy.types.Object`, `bpy.types.Mesh`) over string-based lookups.
- Use `bpy.ops` for invoking built-in operators; pass context overrides via `context_override` dict when the operator needs a specific context.
- Collect undo steps with `bpy.ops.ed.undo_push()` or wrap operations in `context.temp_override()` and `bpy.ops.ed.undo` only when the user's expectation demands manual undo grouping.
- Use `@persistent` decorated handlers (`bpy.app.handlers.load_post`, `save_pre`, `depsgraph_update_post`) for event-driven logic — unregister them in `unregister()`.

## Performance

- Avoid iterating over `bpy.data.objects` or `bpy.data.meshes` in tight loops; cache references to frequently accessed data blocks.
- Use `numpy` for heavy number crunching on mesh data (Blender bundles numpy); access vertex/edge/face arrays via `mesh.vertices[i].co` for individual access or `foreach_get`/`foreach_set` for bulk operations.
- Use `bpy.types.Mesh.validate()` sparingly — it's expensive; call it only after destructive topology changes.
- Batch mesh updates: modify mesh data with `mesh.vertices.foreach_set("co", flat_array)` instead of per-vertex `.co` assignments.
- Profile addon startup time with `bpy.app.handlers.load_post` instrumentation; minimize work done during `register()`.

## Common Pitfalls

- Blender's API is NOT threadsafe; all `bpy` operations must happen on the main thread. Use `ApplicationTimer` or `bpy.app.timers` for deferred execution instead of threads.
- Properties registered with `bpy.utils.register_class()` cannot be unregistered in the same session without restarting Blender; always test with `--factory-startup` flag for clean state.
- `context.active_object` can be `None`; always check before accessing attributes on it.
- `bpy.ops` can fail silently or change context state; call operators in a try-except block when the outcome is uncertain.
- Undo system: Blender's undo tracks changes to data blocks; creating/destroying thousands of data blocks can slow undo to a crawl. Batch operations where possible.
- The `bpy.types.Panel.bl_space_type` and `bl_region_type` must match valid combinations; consult the Blender Python API docs for valid pairings.

## Testing

- Use `pytest` with `pytest-blender` plugin for automated addon testing against a headless Blender instance.
- Write unit tests for utility functions that do not depend on `bpy`; test operator logic by constructing mock contexts.
- Test addon registration (`register()`/`unregister()`) to catch import errors and property collision bugs early.
- Use `addon_utils.enable()` and `addon_utils.disable()` programmatically in test fixtures to load/unload the addon cleanly.

## Export & Interoperability

- Use `bpy.types.Operator` with a `filepath` `StringProperty(subtype='FILE_PATH')` for file export operators.
- When writing exporters, triangulate meshes and apply modifiers with `bpy.ops.object.convert()` or via `bpy.types.Mesh` calculation methods.
- Respect the scene's unit system by converting through `bpy.utils.units.to_value()` before writing to file formats that expect specific units.
