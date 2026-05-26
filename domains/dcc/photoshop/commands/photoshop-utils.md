## /photoshop-utils — Photoshop Utility & Reference Guide

Slash command for quick access to API documentation, version compatibility checks, ExtendScript→UXP migration reference, and reusable code snippets across all Photoshop development surfaces (ExtendScript/JSX, UXP/PSJS, C++ SDK).

---

### Usage

```
/photoshop-utils docs <query>              — Look up API documentation
/photoshop-utils version <api> [versions]   — Check API version compatibility
/photoshop-utils migrate <api|pattern>      — Show ExtendScript→UXP migration mapping
/photoshop-utils snippets <topic>           — Browse code snippet index
/photoshop-utils help                       — Show this help
```

---

### 1. API Documentation Lookup

Opens or searches official Adobe documentation. All queries target adobe.com domains.

| Surface | Primary Docs | Search URL | Quick Reference |
|---------|-------------|-----------|-----------------|
| UXP/PSJS | [Photoshop UXP API Reference](https://developer.adobe.com/photoshop/uxp/2025/) | `https://developer.adobe.com/search/?q=<term>` | [Photoshop UXP Scripting Guide](https://developer.adobe.com/photoshop/scripting/) |
| ExtendScript | [ExtendScript API Reference](https://extendscript.docsforadobe.dev/) | Append `#search=<term>` to ref URL | [Adobe Scripting Guide](https://helpx.adobe.com/photoshop/using/scripting.html) |
| C++ SDK | [Photoshop SDK Docs](https://developer.adobe.com/photoshop/sdk/) | `https://developer.adobe.com/search/?q=<term>+photoshop+sdk` | [SDK GitHub](https://github.com/AdobeDocs/photoshop-sdk) |
| action descriptors | [Action Manager Reference](https://developer.adobe.com/photoshop/uxp/2025/ps_action/) | Via UDT action recording | Scripting Listener plugin |
| manifest schema | [Manifest Config](https://developer.adobe.com/photoshop/uxp/2025/manifest/) | — | UDT > Validate |

**Search helpers:**

- `/photoshop-utils docs batchPlay` — Opens batchPlay reference on adobe.com
- `/photoshop-utils docs layer.create` — Searches Adobe Developer for layer creation APIs
- `/photoshop-utils docs executeAction` — Shows ExtendScript→UXP equivalent and links

**Note:** Offline API documentation is not included. All lookups target live Adobe-hosted documentation.

---

### 2. Version Compatibility

Photoshop version surface support matrix (from rules/photoshop.md):

| Surface | PS 2022 (v23) | PS 2023 (v24) | PS 2024 (v25) | PS 2025 (v26) | PS 2026 (v27) |
|---------|:---:|:---:|:---:|:---:|:---:|
| ExtendScript | ✓ | ✓ | ✓ | ✓ | ✓ |
| UXP (manifest v4, apiVersion 2) | ✓ | ✓ | ✓ | ✓ | ✓ |
| UXP (manifest v5, permissions model) | ✓ (v23.3+) | ✓ | ✓ | ✓ | ✓ |
| UXP (manifest v6) | — | — | ✓ | ✓ | ✓ |
| UXP (batchPlay) | ✓ | ✓ | ✓ | ✓ | ✓ |
| C++ SDK (PIUXPSuite v1) | ✓ (v23.3+) | ✓ | ✓ | ✓ | ✓ |
| C++ SDK (filter/automation) | ✓ | ✓ | ✓ | ✓ | ✓ |

**Annotation pattern for version-dependent APIs:**

```typescript
// @since PS 2024 (v25) — app.activeDocument.artboards
// @removed PS 2023 (v24) — someLegacyAPI()
// @deprecated PS 2025 (v26) — use batchPlay() instead
// @minVersion 24.0 — in manifest.json requiredPermissions block
```

**Changelog references:**

- [Photoshop UXP Changelog](https://developer.adobe.com/photoshop/uxp/changelog/) — API additions, deprecations, removals per version
- [Adobe Community Forums](https://community.adobe.com/t5/photoshop-ecosystem/bd-p/photoshop-ecosystem) — Version-specific issues and workarounds
- GitHub [AdobeDocs/uxp-photoshop](https://github.com/AdobeDocs/uxp-photoshop) releases — SDK update notes

**Usage:**

```
/photoshop-utils version batchPlay v23      — Check batchPlay in PS 2022
/photoshop-utils version "manifest v5"      — Show when manifest v5 was introduced
/photoshop-utils version executeAsModal     — Show version requirements for executeAsModal
```

---

### 3. ExtendScript → UXP Migration

#### Key Differences

| # | ExtendScript (.jsx) | UXP (.psjs) | Notes |
|---|--------------------|-------------|-------|
| 1 | `executeAction(stringID, descriptor, dialogModes)` | `batchPlay([actionDescriptor], { modalBehavior })` | `batchPlay` accepts an array of descriptors; synchronous in ExtendScript, async in UXP |
| 2 | `executeActionGet(reference)` | `batchPlay([{ _obj: "get", _target: reference }])` | Wrapped as a single-element batchPlay array |
| 3 | `app.documents.length > 0` guard before `app.activeDocument` | `app.activeDocument` returns `undefined` — check with `if (app.activeDocument)` | UXP eliminates the runtime throw; no `documents.length` property needed |
| 4 | `$.writeln(message)` | `console.log(message)` | UXP uses standard web console; output visible in UDT Developer Console |
| 5 | `app.doScript(actionName, descriptor, dialogModes)` | `batchPlay([...])` inside `executeAsModal()` | No direct `doScript` equivalent; use batchPlay with the recorded action |
| 6 | `app.activeDocument.suspendHistory(undoName, actionString)` | `executeAsModal()` handles undo grouping automatically | UXP modal scope creates a single undo step; no manual `suspendHistory` call |
| 7 | `app.open(File(path))` | `require('photoshop').core.openFile(path)` or `require('uxp').storage` token APIs | ExtendScript uses Adobe File object; UXP uses storage-capability-based access |
| 8 | `charIDToTypeID("char")` / `stringIDToTypeID("s")` | `require('photoshop').action.charIDToTypeID()` / `.stringIDToTypeID()` | API moved from global scope to `photoshop.action` module |
| 9 | `ScriptUI` dialog with `Window` and UI resources | HTML template + [Spectrum Web Components](https://opensource.adobe.com/spectrum-web-components/) | ExtendScript builds native OS dialogs; UXP renders in Chromium panel with CSS |
| 10 | `#include "helpers.jsxinc"` | `require('./helpers.js')` or ES module `import` | ExtendScript uses preprocessor includes; UXP uses CommonJS/ES modules |
| 11 | `#target photoshop` directive at file top | `manifest.json` `"host": { "app": "PS", "minVersion": "23.0.0" }` | UXP registration moves from script-level directive to plugin manifest |
| 12 | `app.activeDocument.layers[i]` (synchronous array index) | `await doc.layers[i]` or `doc.layers.get(i)` | UXP layer access may require `await` for async collection resolution |
| 13 | ES3: `var` only, no arrow functions, no `Promise` | Modern JS: `let`/`const`, arrow functions, `async/await`, `Promise` | UXP runs on Chromium v102+ engine with full ES2022 support |
| 14 | `alert(message)` / `confirm(message)` (ExtendScript built-in) | `app.showAlert(message)` | UXP has no `window.alert()`; use `photoshop.app.showAlert()` |

#### Execution Model Migration

```
ExtendScript (synchronous)                    UXP (async + modal)
══════════════════════════                    ════════════════════════
var doc = app.activeDocument;                 const doc = app.activeDocument;
doc.resizeImage(800, 600);                    await require('photoshop').core.executeAsModal(
                                                async () => { doc.resizeImage(800, 600); }
                                              );
```

**Critical rule:** ALL document-modifying operations in UXP require an `executeAsModal` wrapper. Omitting it causes silent failure — no error is thrown, the operation simply does not execute.

#### API Equivalence Validation

When migrating specific APIs:
1. Check if the API exists in the [UXP DOM](https://developer.adobe.com/photoshop/uxp/2025/ps_app/) — prefer DOM over batchPlay
2. If not in DOM, record the action with Photoshop Scripting Listener, then translate the descriptor to batchPlay format
3. Use the `ps-es-to-uxp` logger utility (referenced in rules) to auto-convert ExtendScript action descriptor calls
4. Validate descriptor JSON structure before executing — `batchPlay` does not error on mismatched keys

---

### 4. Code Snippets Index

Refer to `domains/dcc/photoshop/rules/photoshop.md` for canonical patterns. Below is an index of common operation code templates organized by task.

| Topic | Surface | Description |
|-------|---------|-------------|
| Document guard | UXP | `if (!app.activeDocument) return;` — check before any doc operation |
| Document guard | ES | `if (app.documents.length > 0) { var doc = app.activeDocument; }` |
| Create layer | UXP | `await doc.createLayer({ name: "New Layer" })` inside `executeAsModal` |
| Create layer | ES | `var layer = doc.artLayers.add(); layer.name = "New Layer";` |
| Iterate layers | UXP | `for (const layer of doc.layers) { ... }` |
| Iterate layers | ES | `for (var i = 0; i < doc.layers.length; i++) { ... }` |
| Save document | UXP | `await doc.save()` or `await doc.saveAs(saveToken)` with storage token |
| Save document | ES | `doc.saveAs(File(folder + "/output.psd"));` |
| Batch operation | UXP | Group multiple ops in one `batchPlay([desc1, desc2, ...])` call |
| User message | UXP | `app.showAlert("Message")` |
| User message | ES | `alert("Message")` |
| Logging | UXP | `console.log(value)` — viewed in UDT Developer Console |
| Logging | ES | `$.writeln(value)` — viewed in ESTK Console |
| Undo step | UXP | Automatic via `executeAsModal` scope |
| Undo step | ES | `suspendHistory("Step Name", "code string")` |
| Filter layer style | ES | `doc.activeLayer.applyStyle(styleName)` |
| Action descriptor | UXP | `require('photoshop').action` — `stringIDToTypeID`, `putInteger`, etc. |
| Action descriptor | ES | `stringIDToTypeID` in global scope, `ActionDescriptor` class |
| Open file | UXP | `require('photoshop').core.openFile(path)` |
| Open file | ES | `app.open(File(path))` |
| Close doc | UXP | `await doc.close()` inside `executeAsModal` |
| Close doc | ES | `doc.close(SaveOptions.DONOTSAVECHANGES)` |
| Access manifest host | UXP | `require('photoshop').host.descriptor` — plugin host metadata |

**Template variables** (replace per use):
- `doc` — active document reference
- `path` — file system path string
- `saveToken` — UXP storage token from `require('uxp').storage`
- `actionName` / `stepName` — user-visible undo step text

---

### 5. External Resources

| Resource | URL |
|----------|-----|
| Adobe Developer — Photoshop UXP | [https://developer.adobe.com/photoshop/uxp/](https://developer.adobe.com/photoshop/uxp/) |
| Adobe Developer — Photoshop Scripting | [https://developer.adobe.com/photoshop/scripting/](https://developer.adobe.com/photoshop/scripting/) |
| Adobe Developer — Photoshop SDK | [https://developer.adobe.com/photoshop/sdk/](https://developer.adobe.com/photoshop/sdk/) |
| ExtendScript API Reference | [https://extendscript.docsforadobe.dev/](https://extendscript.docsforadobe.dev/) |
| Adobe UXP Photoshop GitHub | [https://github.com/AdobeDocs/uxp-photoshop](https://github.com/AdobeDocs/uxp-photoshop) |
| Photoshop SDK GitHub | [https://github.com/AdobeDocs/photoshop-sdk](https://github.com/AdobeDocs/photoshop-sdk) |
| Spectrum Web Components | [https://opensource.adobe.com/spectrum-web-components/](https://opensource.adobe.com/spectrum-web-components/) |
| Adobe Community — Photoshop Ecosystem | [https://community.adobe.com/t5/photoshop-ecosystem/bd-p/photoshop-ecosystem](https://community.adobe.com/t5/photoshop-ecosystem/bd-p/photoshop-ecosystem) |
