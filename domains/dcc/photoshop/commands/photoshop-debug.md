## `/photoshop-debug` — Photoshop Run & Debug Guidance

> **⚠️ Capability statement**: This command provides **documentation guidance** on how to run and debug Photoshop scripts and plugins. It does **NOT** run scripts in Photoshop directly, attach to processes, or provide real-time breakpoint debugging. All debug operations require the developer to use the appropriate Adobe tools on their local machine.

---

### 1. ExtendScript (.jsx) Run & Debug

#### Running ExtendScript

| Method | Steps |
|--------|-------|
| **Photoshop Menu** | `File > Scripts > Browse…` → select `.jsx` file → Open |
| **Command Line** | `photoshop.exe script.jsx` (note: Photoshop must be closed for CLI launch, or the script runs in the next startup) |
| **Drag & Drop** | Drag `.jsx` onto Photoshop icon (launches Photoshop and runs script) |
| **ESTK / ExtendScript Toolkit** | Open `.jsx` in ESTK → `Debug > Run` (requires ESTK installed; last bundled with Photoshop CC 2019) |

#### Debugging ExtendScript

- **ExtendScript Debugger (ESTK)**: Bundled in older Photoshop versions. Step-through debugging, variable inspection, and `$.writeln()` console output in the **JavaScript Console** tab.
- **VS Code ExtendScript Debug extension**: Community extension providing breakpoints, call stack, and variable watch. Configure a launch task pointing to your script path.
- **Scripting Listener plug-in**: Adobe's diagnostic plug-in that records all Photoshop actions as script code. Enable via Photoshop's `Plug-ins > Scripting Listener`. The output (JavaScript log) shows the exact API calls the UI triggers — invaluable for reverse-engineering workflows.
- **Error catching wrapper**: Wrap top-level code in a try-catch that writes to both `$.writeln()` and an external log file:
  ```javascript
  try {
      // main script logic
  } catch (e) {
      $.writeln("Error: " + e);
      var logFile = File("~/desktop/script-error.log");
      logFile.open("w");
      logFile.writeln("Error: " + e + "\n" + e.stack);
      logFile.close();
  }
  ```

---

### 2. UXP (.psjs / panel) Run & Debug

#### Running UXP Plugins

| Method | Steps |
|--------|-------|
| **UXP Developer Tool (UDT)** | Open UDT → `Add Plugin` → select your `manifest.json` folder → `Actions > Load`. Plugin appears in Photoshop's `Plugins > <name>` menu. |
| **Side-load** | Copy built plugin folder to `~/Creative Cloud/CCX/Plug-ins/` — Photoshop loads it on next restart. |

> **Note**: UDT is an Electron app shipped with Adobe UXP Developer Toolkit. If not installed, use side-loading or install via the [Adobe UXP Developer Tool page](https://developer.adobe.com/uxp/docs/tools/devtool/).

#### Debugging UXP Plugins

- **UDT Developer Console**: After loading a plugin via UDT, click `Developer Console` to view `console.log()`, `console.warn()`, and `console.error()` output from your UXP plugin.
- **Chrome DevTools Protocol**: Connect DevTools to a loaded plugin via UDT:
  1. In UDT, click **Actions** → **Inspect** on your loaded plugin.
  2. A DevTools window opens with Elements, Console, Sources, and Network tabs.
  3. Set breakpoints directly in the Sources panel.
- **Photoshop menu**: `Plugins > Development > UXP Developer Tool` opens UDT within Photoshop (UDT must be installed and running).
- **Logging best practice**: Prefix logs with plugin ID for multi-plugin projects:
  ```javascript
  const LOG_TAG = "[MyPlugin]";
  console.log(LOG_TAG, "Initializing...");
  ```

---

### 3. Log Viewing

| Surface | Log Output | How to View |
|---------|-----------|-------------|
| **ExtendScript** | `$.writeln("message")` | ESTK JavaScript Console / VS Code Debug Console |
| **ExtendScript** | `$.global["catch"]` error handler | Wrap in try-catch, write to `File` object |
| **UXP** | `console.log("message")` | UDT Developer Console / Chrome DevTools Console |
| **UXP** | `app.showAlert("message")` | Photoshop alert dialog (user-facing only, not for debug) |
| **C++ SDK** | `FilterRecord::errorString` | Photoshop shows error in UI; also logged to system event log on Windows |
| **Scripting Listener** | Action descriptor output | Photoshop's Scripting Listener plug-in log |
| **External file** | Custom file logging | Write to `~/Desktop/` or `~/Documents/` with `File` (ExtendScript) or `require('uxp').storage` (UXP) |

---

### 4. Common Error Scenarios & Troubleshooting

#### Scenario 1: "Permission denied" — UXP filesystem/network API fails
- **Cause**: Manifest v5+ requires explicit `requiredPermissions` — missing `"localFileSystem"`, `"network"`, etc.
- **Fix**: Add to `manifest.json`:
  ```json
  "requiredPermissions": {
      "localFileSystem": "readWrite",
      "network": [ "domains" ]
  }
  ```
- **Verify**: Re-load plugin in UDT after editing manifest.

#### Scenario 2: "API unavailable" — UXP DOM method returns `undefined`
- **Cause**: Calling a DOM API not available in the target Photoshop version (e.g., `doc.createLayer()` in PS v22).
- **Fix**: Check the API against the version compatibility table. Fall back to `batchPlay()` for APIs not exposed in the DOM. Always guard:
  ```javascript
  if (typeof app.activeDocument?.createLayer === 'function') {
      await doc.createLayer({ name: "New" });
  } else {
      // fallback to batchPlay
  }
  ```

#### Scenario 3: Version mismatch — ExtendScript `#target` directive ignored
- **Cause**: `#target photoshop` missing or misspelled (e.g., `#target photoshop2024`). Script runs in the wrong host or fails silently.
- **Fix**: Ensure first line of entry `.jsx` is exactly `#target photoshop`. This is required for file-launch (double-click / drag-drop) cross-platform compatibility.

#### Scenario 4: Silent failure — UXP `executeAsModal` not used
- **Cause**: Document-modifying code (e.g., `doc.createLayer()`, `doc.save()`) called outside `executeAsModal`. No error is thrown — the operation silently does nothing.
- **Fix**: Wrap all document-modifying operations:
  ```javascript
  await require('photoshop').core.executeAsModal(async (ctx) => {
      const doc = app.activeDocument;
      const newLayer = await doc.createLayer({ name: "Result" });
  });
  ```

#### Scenario 5: "No documents open" — ExtendScript throws on `app.activeDocument`
- **Cause**: Accessing `app.activeDocument` when `app.documents.length === 0` throws a runtime error.
- **Fix**: Always guard:
  ```javascript
  if (app.documents.length > 0) {
      var doc = app.activeDocument;
  } else {
      alert("Please open a document first.");
  }
  ```

#### Scenario 6: UXP load failure — manifest validation error
- **Cause**: `manifest.json` has schema errors (missing fields, wrong `icon` paths, invalid `requiredPermissions` format).
- **Fix**: Validate before loading:
  - UDT: `Operations > Validate` on your plugin.
  - Automated: Use `npm run validate` if using the UXP CLI template. Check `manifestVersion` >= 4 and `host.app` contains `"PS"`.

#### Scenario 7: Script runs but produces wrong results — action descriptor key mismatch
- **Cause**: `batchPlay()` or `executeAction()` called with incorrect descriptor keys (e.g., `"null"` instead of `"nullUnit"`). No error is thrown — the action silently applies to the wrong target.
- **Fix**: Log the descriptor JSON before executing:
  ```javascript
  console.log(JSON.stringify(descriptor, null, 2));
  ```
  Compare against Scripting Listener output for the equivalent manual operation.

---

### 5. Quick Reference

```bash
# Run ExtendScript via Photoshop file menu
# File > Scripts > Browse... > select .jsx

# Debug UXP via UDT
# UXP Developer Tool > Add Plugin > Actions > Load > Developer Console

# Enable Scripting Listener
# Photoshop > Plug-ins > Scripting Listener > Enable JavaScript Logging

# Validate UXP manifest
# UXP Developer Tool > Operations > Validate

# Common log locations
# ExtendScript: ESTK Console ($.writeln)
# UXP: UDT Console (console.log)
# External: custom File write to ~/Desktop/script-error.log
```
