# Autodesk Maya DCC Development Rules

Rules for AI-assisted Autodesk Maya tool and plugin development with Python and C++. Follow these in every Maya scripting project.

## Project Structure

- Place Maya scripts under the Maya scripts directory (`~/maya/<version>/scripts/`) or a custom `MAYA_SCRIPT_PATH` for version-controlled development.
- Structure tools as Maya modules (`.mod` files) with `scripts/`, `plug-ins/`, `icons/`, and `presets/` subdirectories.
- Use `userSetup.py` for session initialization and `userSetup.mel` only when MEL-exclusive APIs require it.
- Separate UI code (PySide2/PySide6 or PyMel UI commands) from core logic; never couple Maya API calls directly to widget callbacks.
- Prefix custom nodes and commands with a project-specific namespace to avoid collisions with other tools.

## Python Coding Conventions

- Target Python 3.9+ (Maya 2022+) or Python 3.7+ (Maya 2020-2021); check the target Maya version before using newer Python features.
- Prefer `maya.api.OpenMaya` (OpenMaya 2.0) over `maya.OpenMaya` (OpenMaya 1.0) for all new C++ API wrappers — it returns Python objects instead of MScriptUtil values.
- Use `cmds` for high-level scene operations, `pymel` for object-oriented workflows, and `OpenMaya` for performance-critical low-level operations.
- Always wrap `cmds.file()` operations in try-except blocks; file operations are the most common source of unhandled Maya exceptions.
- Use `contextlib.contextmanager` to create undo chunks with automatic cleanup; pair `cmds.undoInfo(openChunk=True)` with a `finally` clause calling `cmds.undoInfo(closeChunk=True)`.

## API Usage Patterns

- Use `maya.api.OpenMaya.MFnDependencyNode` and related `MFn*` function sets for C++ API-level node manipulation; these are faster than `cmds` for batch operations.
- Use `cmds.evalDeferred()` to defer UI or scene operations to the next idle event; critical for avoiding "Object does not exist" errors during scene construction.
- Prefer `pymel.core.PyNode` for convenient string-to-node resolution when prototyping; switch to `OpenMaya.MObject` handles in production code for stability.
- Use `maya.api.OpenMaya.MDGModifier` for building dependency graph connections programmatically; it avoids the overhead of repeated `cmds.connectAttr()` calls.
- Leverage `cmds.scriptJob()` for event-driven callbacks; always store the job ID and kill it on tool shutdown to prevent zombie callbacks.

## Performance

- Batch operations: use `cmds.select()` + multi-object commands rather than looping over individual object operations.
- Use `maya.api.OpenMaya.MItMeshVertex` / `MItMeshPolygon` iterators instead of calling `cmds.getAttr()` per-component in loops.
- Avoid `cmds.refresh()` in performance-critical code; only call it when the viewport must update before continuing.
- For heavy mesh or animation processing, write the work in a C++ plugin (`MPxNode` or `MPxCommand`); Python is 10-100x slower for dense data processing.
- Profile with `maya.mel.eval("timerX")` or `cProfile` wrapped around critical code paths; Maya's `dgtimer` is unreliable for fine-grained measurement.

## Common Pitfalls

- Maya's undo system flushes on scene new/open/import; never leave undo chunks open across file operations.
- `cmds.select()` changes the global selection state; save and restore selection with `cmds.ls(selection=True)` wrapped in try-finally.
- `cmds.listRelatives()` and `cmds.listConnections()` return `None` when no results exist; always check for `None` before iterating.
- DAG paths vs. dependency node names: the same node can have multiple DAG paths if instanced; use `MFnDagNode.getPath()` to enumerate all paths.
- MEL and Python namespace scoping differs; MEL commands run in the global MEL scope regardless of Python's namespace.
- `cmds.confirmDialog()` blocks the main thread; use `cmds.layoutDialog()` or PySide dialog for non-blocking UIs.

## Testing

- Use `pytest` with the `maya-standalone` Python interpreter for headless tests; invoke via `mayapy -m pytest tests/`.
- Mock Maya dependencies with `unittest.mock` for unit tests of pure-logic components; integration tests should run against a real Maya session.
- Test tool registration and deregistration as separate test cases to catch leaked callbacks and orphaned UI elements.
- Use temporary scenes created via `cmds.file(new=True, force=True)` in test fixtures; never leave the Maya session in a dirty state after tests.

## UI Development

- Use PySide2 (Maya 2017-2024) or PySide6 (Maya 2025+) for all tool UIs; avoid `cmds.window()` / `cmds.columnLayout()` for complex UIs.
- Subclass `QWidget` or `QDialog` and wrap the Maya main window with `maya.OpenMayaUI.MQtUtil.mainWindow()` for proper parent-child window management.
- Use Maya's `workspaceControl` (Maya 2017+) for dockable tool windows; fall back to `cmds.window()` only for legacy compatibility.
- Style tool UIs with Maya's internal stylesheet classes rather than hardcoded colors; use `cmds.themeColor()` to query the current theme colors.
