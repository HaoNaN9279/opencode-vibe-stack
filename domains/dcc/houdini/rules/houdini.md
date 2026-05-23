# SideFX Houdini DCC Development Rules

Rules for AI-assisted Houdini tool and HDA development with Python and VEX. Follow these in every Houdini scripting project.

## Project Structure

- Store HDA (Houdini Digital Asset) definitions in `otls/` directories or version-controlled `.hda` files alongside your Python tools.
- Structure Python code under `scripts/python/` with a package namespace (e.g., `my_studio.houdini.tools`) to avoid import conflicts.
- Use Houdini packages (`.json` files in `~/houdini<version>/packages/`) to configure `HOUDINI_PATH` entries; never hardcode paths in `houdini.env`.
- Separate tools by domain: `scripts/python/tools/` for shelf tools, `scripts/python/pdg/` for PDG nodes, `scripts/python/hdas/` for HDA Python modules.
- Keep VEX code in `.vfl` or `.h` header files within the HDA; use `#include` directives for shared VEX code.

## Python Coding Conventions

- Target Python 3.9+ (Houdini 19.0+) or Python 3.11+ (Houdini 20.5+); Houdini bundles its own Python, so check `sys.version` on import.
- Use `hou` module for all Houdini-specific operations; avoid subprocess calls to `hscript` or `hython` from within a running session.
- Access nodes via `hou.node("/path/to/node")` or `hou.nodeBySessionId()` for persistent references; never store `hou.Node` references across scene closures.
- Use `hou.Parm.set()` with keyword arguments for parameter groups; it's more efficient than setting individual parms.
- Wrap long-running operations in `hou.ui.displayMessage()` or progress bars via `hou.ui.createProgressBar()` to communicate status to the user.

## API Usage Patterns

- Use `hou.Node.createNode()` for programmatic node creation; specify `node_name` parameter to set a predictable name.
- Wire nodes with `node.setInput(index, upstream_node)` or `node.setNextInput(upstream_node)` for chain workflows.
- Use `hou.ParmTemplateGroup` and `hou.ParmTemplate` subclasses to programmatically build HDA parameter interfaces.
- Leverage `hou.PythonPanelInterface` for custom panels and `hou.PyPanel` for embedding Python UI into Houdini panes.
- Use `hou.HDAModule` for Python modules embedded within HDAs; import them with `hou.session` or `hou.hda.definitions()`.
- For PDG (Procedural Dependency Graph), use `pdg.TypeRegistry` and subclass `pdg.types.Node` for custom PDG node types.

## Performance

- Use `hou.Geometry.setPointFloatAttribValues()` and `hou.Geometry.setPrimFloatAttribValues()` for bulk attribute setting instead of per-element iteration.
- Prefer VEX/CVEX over Python for geometry processing inside node networks; Python snippet nodes are for glue logic, not per-point computation.
- Use `hou.Geometry.freeze()` and `hou.Geometry.unfreeze()` around batch geometry modifications to suppress cook events during construction.
- Cache expensive computations with `hou.HDAModule` class-level variables; Houdini reloads the module on HDA updates, clearing stale caches automatically.
- Profile Python code with `cProfile` integrated via `hou.session`; for VEX, use the Performance Monitor (Windows > Performance Monitor).

## Common Pitfalls

- `hou.Node` objects become invalid after the node is deleted or the scene is closed; always call `node.isValid()` or use try-except before accessing methods.
- Houdini's cooking is lazy; calling `node.cook(force=True)` forces an upstream cook chain. Use `node.cook()` (without force) to cook only when dirty.
- Parameter expressions using backtick syntax (`` `chs("../other")` ``) evaluate in Hscript context, not Python; use `hou.parm().eval()` or Python expressions for modern parameter references.
- `hou.Parm.eval()` returns the raw parameter value at the current time; use `hou.Parm.evalAtFrame(float)` to evaluate at a specific frame.
- The Python `__file__` attribute is unreliable inside HDA Python Modules; use `hou.session` module inspection or `inspect.getfile()` instead.
- Undo is HDA-level only; Python-side state changes (global variables, file modifications) are NOT covered by Houdini's undo system.

## VEX & CVEX

- Use `@`-syntax for attribute binding in VEX snippets (`@P`, `@Cd`, `@myattrib`); explicitly declare types with `f@`, `i@`, `v@`, `p@`, `s@` prefixes.
- Keep VEX wrangles small and focused; split complex operations across multiple wrangle nodes for maintainability and incremental cooking.
- Use `setpointattrib()`, `setprimattrib()`, `setdetailattrib()` for writing attributes; never use `addattrib()` inside a running VEX loop — it invalidates attribute handles.
- Leverage `while()` loops with `pointlist()` in VEX for neighbor lookups; avoid `nearpoints()` in hot loops when you only need connected vertices.
- Use `chi()` and `chf()` for channel references in VEX; they auto-create parameter interfaces on the wrangle node.

## Testing

- Use `pytest` with `hython` for headless Houdini test execution: `hython -m pytest tests/`.
- Write unit tests against `hou` API calls using `unittest.mock` where the Houdini session is not required; integration tests create scenes via `hou.hipFile.clear()`.
- Test HDA parameter validation by instantiating the HDA programmatically and calling `.parm().set()` with edge-case values.
- Use snapshot-based testing for geometry output: hash the vertex positions of cooked nodes and compare against known-good hashes.

## HDA Development

- Define the HDA operator table and label clearly in the Type Properties dialog; use `Create/Modify > Digital Asset > New Digital Asset From Selection`.
- Embed a `OnCreated` Python script in the HDA to set default parameter values and create initial internal node networks.
- Use `hou.HDAOptions` to set the save mode to `HDAOptions.MixedSaveMode` for iterating on Python code without re-saving the HDA binary unless node changes occur.
- Version HDAs with semantic versioning in the HDA's `Version` field; store the version history in the HDA's `Help` tab as markdown.
