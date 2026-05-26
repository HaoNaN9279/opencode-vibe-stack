# `/photoshop-create` — Photoshop Project Scaffolding

> **This is a guidance document, not an automated execution tool.**  
> It instructs AI agents on the correct directory structures, file templates, and manifest configurations to generate when scaffolding a new Photoshop development project. No software installation, Photoshop runtime invocation, or build execution is performed.

---

## 1. 用途

Scaffold a new Photoshop development project in one of three surface types:

| Sub-command | Surface | Use Case |
|---|---|---|
| `extendscript` | ExtendScript (.jsx) | Quick scripts, batch processing, legacy automation |
| `uxp` | UXP (.psjs + manifest.json) | Modern panel/script plugins with UI, permissions model |
| `cpp` | C++ SDK (.cpp/.h) | High-performance filters, format handlers, hybrid UXP+C++ |

The AI agent generates the directory tree, entry-point files, and (for UXP) a valid `manifest.json` matching the requested version. The user specifies the project name, surface type, and optional parameters.

---

## 2. 用法

```
/photoshop-create extendscript --name <project-name> [--version <x.y.z>]
/photoshop-create uxp --name <project-name> --type <panel|script|headless> [--manifest-version <4|5|6>] [--framework <react|vue|none>] [--host-min <x.y.z>]
/photoshop-create cpp --name <project-name> [--sdk-version <2025|2026>]
```

### Shorthand form

```
/create ps-es --name BatchResize --version 1.0.0
/create ps-uxp --name LayerManager --type panel --manifest-version 5
/create ps-cpp --name CustomFilter --sdk-version 2025
```

---

## 3. 参数

### Global parameters

| Parameter | Required | Description |
|---|---|---|
| `--name` | Yes | Project name (used for directory name, entry file names, and manifest `id`) |
| `--version` | No | Semantic version string (`x.y.z`). Default: `1.0.0` |

### ExtendScript-specific parameters

| Parameter | Required | Description |
|---|---|---|
| *(none beyond global)* | — | ExtendScript projects have no additional scaffolding parameters. The `#target photoshop` directive is always added. |

### UXP-specific parameters

| Parameter | Required | Description |
|---|---|---|
| `--type` | Yes | Plugin type: `panel` (dockable UI panel), `script` (menu-triggered script), `headless` (no UI). |
| `--manifest-version` | No | Target manifest version: `4`, `5`, or `6`. Default: `5`. See **§6 — manifest.json 模板指南** below. |
| `--framework` | No | UI framework for panel type: `react`, `vue`, or `none`. Default: `none` (vanilla HTML/CSS/JS with Spectrum Web Components). |
| `--host-min` | No | Minimum Photoshop version (e.g., `24.0`, `25.0`). Default: `24.0`. |

### C++ SDK-specific parameters

| Parameter | Required | Description |
|---|---|---|
| `--sdk-version` | No | Target Photoshop SDK version year (e.g. `2025`, `2026`). Default: `2025`. This parameter exists for documentation purposes only — no build configurations or platform toolchain files are generated. |

---

## 4. 执行步骤

### 4.1 ExtendScript project (`extendscript` / `ps-es`)

1. **Create directory structure**

   ```
   <project-name>/
   ├── scripts/          # Entry-point .jsx files
   │   └── <project-name>.jsx
   ├── includes/         # Shared .jsxinc modules
   │   └── <project-name>.jsxinc    (optional, include if helpers exist)
   └── docs/             # Usage documentation
       └── README.md
   ```

2. **Generate entry script** (`scripts/<project-name>.jsx`)

   ```javascript
   // @target photoshop
   // @include "includes/<project-name>.jsxinc"
   // @description <project-name> — <brief description>
   // @version <version>

   (function() {
       'use strict';

       // Guard: ensure at least one document is open
       if (app.documents.length === 0) {
           alert('Please open a document first.');
           return;
       }

       var doc = app.activeDocument;

       // --- Project-specific logic here ---
       $.writeln('Running <project-name> v<version>');

       // Wrap document-modifying operations in suspendHistory for undo support
       doc.suspendHistory('<project-name>', '/* action string here */');

   })();
   ```

   - Line 1 **must** be `#target photoshop` for cross-platform file-launch compatibility.
   - Enclose all logic in an IIFE to avoid global-scope pollution (ES3 restriction: `var` only, no `let`/`const`/arrow functions).
   - Wrap user-facing operations with `doc.suspendHistory()`.
   - Use `$.writeln()` for debug logging.

3. **Generate include module** (`includes/<project-name>.jsxinc`)

   ```javascript
   // @include guard — this file is not standalone
   // Shared helpers for <project-name>

   (function() {
       // Place shared functions here
       // Use .jsxinc extension — Photoshop's ExtendScript engine
       // distinguishes these from standalone .jsx files.
   })();
   ```

4. **Generate docs** (`docs/README.md`) — brief usage instructions referencing the entry script path.

---

### 4.2 UXP project (`uxp` / `ps-uxp`)

1. **Create directory structure**

   ```
   <project-name>/
   ├── src/               # Source code
   │   ├── main.js        # Entry point (required)
   │   ├── <component>.js # Additional modules (as needed)
   │   └── style.css      # Styles (panel type)
   ├── public/            # Static assets
   │   └── icons/
   │       ├── dark-23.png
   │       ├── dark-46.png
   │       ├── light-23.png
   │       └── light-46.png
   ├── dist/              # Built output (empty at scaffold)
   └── manifest.json      # Plugin manifest
   ```

   - **Panel type**: Add `public/icons/` with 23px and 46px PNG icons for dark/light themes.
   - **Script / headless type**: Omit `public/icons/` (no UI chrome).

2. **Generate entry script** (`src/main.js`)

   ```javascript
   'use strict';

   const app = require('photoshop').app;
   const core = require('photoshop').core;

   // --- Plugin logic here ---
   // All document-modifying operations MUST be wrapped in executeAsModal:
   // await core.executeAsModal(async (executionContext) => { ... });

   // Example: log active document info
   if (app.activeDocument) {
       console.log('Active document:', app.activeDocument.name);
   }
   ```

   - Every `.psjs` / `.js` file must begin with `"use strict"`.
   - Import Photoshop DOM via `require('photoshop').app`.
   - Use `core.executeAsModal()` for any document-modifying operation.

3. **Generate manifest.json** — See **§6 — manifest.json 模板指南** below for version-specific templates. Generate the appropriate template based on `--manifest-version`.

4. **Framework setup** (if `--framework react` or `--framework vue`):
   - Generate `src/` with framework entry point (e.g., `index.jsx` for React).
   - Add a `package.json` placeholder with the framework dependency noted.
   - Do NOT run `npm install` — this is a guidance scaffold.

---

### 4.3 C++ SDK project (`cpp` / `ps-cpp`)

> **⚠ Documentation-only scaffold.** No build configurations, platform toolchain files (`.vcxproj`, `.xcodeproj`), or SDK headers are generated. The user must set up the C++ SDK environment manually. For project structure guidance, see `domains/dcc/photoshop/rules/photoshop.md`.

1. **Create directory structure**

   ```
   <project-name>/
   ├── source/            # Source files (.cpp)
   │   └── <project-name>.cpp
   ├── include/           # SDK headers and project headers
   │   └── <project-name>/
   │       └── Plugin.h
   ├── resources/         # PiPL resource files, icons, version info
   │   └── <project-name>.r
   └── docs/              # Build and architecture notes
       └── BUILD.md
   ```

2. **Generate source file** (`source/<project-name>.cpp`)

   ```cpp
   // <project-name> — Photoshop C++ SDK Plugin
   // Target SDK: Photoshop <sdk-version>
   //
   // NOTE: This is a structural skeleton. Suite acquisition, descriptor
   // construction, and error handling are the responsibility of the developer.

   #include "PSPlugIn.h"
   #include "PITypes.h"
   #include "PIActionDescriptor.h"

   // Entry point (filter plugin example)
   DLLExport SPAPI PluginMain(const short selector,
                              FilterRecordPtr filterRecord,
                              long* data,
                              short* result) {
       // Suite acquisition pattern:
       // SPBasicSuite* sSPBasic = filterRecord->sSPBasic;
       // sSPBasic->AcquireSuite(kSomeSuite, kSomeVersion, (const void**)&suitePtr);
       //
       // Must check kSPNoError return and Free() all acquired suites.
       // Memory from suite Make() calls must be explicitly released.
   }
   ```

3. **Generate resource file** (`resources/<project-name>.r`)

   ```
   // PiPL resource — defines plugin type and entry functions
   // Types: filter (.8bf), automation, format, import, export
   // Entry: PluginMain (filter), AutoPluginMain (automation)
   ```

4. **Generate build notes** (`docs/BUILD.md`) — placeholder directing the user to:
   - Set up the Photoshop C++ SDK environment.
   - Open the platform project in Visual Studio (Windows) or Xcode (macOS).
   - Build and copy the resulting `.8bf` / `.plugin` to Photoshop's `Plug-ins/` directory.

---

## 5. 输出

The command produces a fully-scaffolded directory tree at the user's specified location (default: current working directory). The AI agent explicitly lists every created file and its purpose.

**Example output (ExtendScript):**

```
Created project "BatchResize" at ./BatchResize/
├── scripts/BatchResize.jsx        — Entry script (#target photoshop, IIFE wrapper)
├── includes/BatchResize.jsxinc    — Shared helpers module
└── docs/README.md                 — Usage documentation
```

**Example output (UXP):**

```
Created project "LayerManager" at ./LayerManager/
├── src/
│   ├── main.js                     — Entry point (executeAsModal-wrapped)
│   └── style.css                   — Plugin styles (Spectrum Web Components tokens)
├── public/icons/
│   ├── dark-23.png                 — Dark theme icon (23px)
│   ├── dark-46.png                 — Dark theme icon (46px)
│   ├── light-23.png                — Light theme icon (23px)
│   └── light-46.png                — Light theme icon (46px)
├── dist/                           — Build output (empty)
└── manifest.json                   — Manifest v5 (requiredPermissions block)
```

**Example output (C++ SDK):**

```
Created project "CustomFilter" at ./CustomFilter/
├── source/CustomFilter.cpp         — Source skeleton (PluginMain entry)
├── include/CustomFilter/Plugin.h   — Project header
├── resources/CustomFilter.r        — PiPL resource stub
└── docs/BUILD.md                   — Build instructions placeholder
```

---

## 6. manifest.json 模板指南

Generate the appropriate manifest version based on `--manifest-version` parameter.

### manifest v4 (Photoshop 2022+, `--manifest-version 4`)

```json
{
    "manifestVersion": 4,
    "id": "<PREFIX>.<PROJECT_NAME>",
    "name": "<Project Display Name>",
    "version": "<VERSION>",
    "main": "index.html",
    "host": {
        "app": "PS",
        "minVersion": "<HOST_MIN>"
    },
    "entrypoints": [
        {
            "type": "panel",
            "id": "panel",
            "label": "<Project Display Name>",
            "minimumSize": { "width": 300, "height": 400 },
            "preferredDockedSize": { "width": 350, "height": 500 }
        }
    ],
    "icons": [
        { "width": 23, "height": 23, "path": "icons/dark-23.png", "theme": "dark" },
        { "width": 46, "height": 46, "path": "icons/dark-46.png", "theme": "dark" },
        { "width": 23, "height": 23, "path": "icons/light-23.png", "theme": "light" },
        { "width": 46, "height": 46, "path": "icons/light-46.png", "theme": "light" }
    ]
}
```

**Notes:**
- `apiVersion` defaults to 2 for `minVersion >= 23.0`.
- No `requiredPermissions` block — filesystem/network APIs are inaccessible.
- Suitable for plugins that do not require filesystem or network access.
- `entrypoints` type is `"panel"` for panel plugins, `"script"` for script plugins, or omitted for headless.

### manifest v5 (Photoshop 2023+, `--manifest-version 5`, default)

```json
{
    "manifestVersion": 5,
    "id": "<PREFIX>.<PROJECT_NAME>",
    "name": "<Project Display Name>",
    "version": "<VERSION>",
    "main": "index.html",
    "host": {
        "app": "PS",
        "minVersion": "<HOST_MIN>"
    },
    "entrypoints": [
        {
            "type": "panel",
            "id": "panel",
            "label": "<Project Display Name>",
            "minimumSize": { "width": 300, "height": 400 },
            "preferredDockedSize": { "width": 350, "height": 500 }
        }
    ],
    "icons": [
        { "width": 23, "height": 23, "path": "icons/dark-23.png", "theme": "dark" },
        { "width": 46, "height": 46, "path": "icons/dark-46.png", "theme": "dark" },
        { "width": 23, "height": 23, "path": "icons/light-23.png", "theme": "light" },
        { "width": 46, "height": 46, "path": "icons/light-46.png", "theme": "light" }
    ],
    "requiredPermissions": {
        "localFileSystem": ["read", "save"],
        "network": ["communication"]
    }
}
```

**Notes:**
- `requiredPermissions` is **required** in v5. Undeclared permissions are denied at install time with no runtime fallback.
- Add only the minimum permissions the plugin actually needs (principle of least privilege).
- `"localFileSystem"` permission is needed for `require('uxp').storage.localFileSystem.getFolder()`.
- `"network"` permission is needed for any `fetch()` or HTTP communication.

### manifest v6 (Photoshop 2024+, `--manifest-version 6`)

```json
{
    "manifestVersion": 6,
    "id": "<PREFIX>.<PROJECT_NAME>",
    "name": "<Project Display Name>",
    "version": "<VERSION>",
    "main": "index.html",
    "host": {
        "app": "PS",
        "minVersion": "<HOST_MIN>"
    },
    "entrypoints": [
        {
            "type": "panel",
            "id": "panel",
            "label": "<Project Display Name>",
            "minimumSize": { "width": 300, "height": 400 },
            "preferredDockedSize": { "width": 350, "height": 500 }
        }
    ],
    "icons": [
        { "width": 23, "height": 23, "path": "icons/dark-23.png", "theme": "dark" },
        { "width": 46, "height": 46, "path": "icons/dark-46.png", "theme": "dark" },
        { "width": 23, "height": 23, "path": "icons/light-23.png", "theme": "light" },
        { "width": 46, "height": 46, "path": "icons/light-46.png", "theme": "light" }
    ],
    "requiredPermissions": {
        "localFileSystem": ["read", "save"],
        "network": ["communication"]
    }
}
```

**Notes:**
- v6 is identical in structure to v5 but may introduce new schema properties in future Photoshop releases.
- Available from Photoshop 2024 (v25) onward (see compatibility table in `rules/photoshop.md`).

### Version compatibility reference

| Manifest | Photoshop | apiVersion | Key change |
|---|---|---|---|
| v4 | 2022+ (v23) | 2 (auto) | Base UXP manifest |
| v5 | 2023+ (v24) | 2 (auto) | `requiredPermissions` block mandatory |
| v6 | 2024+ (v25) | 2 (auto) | Future-proofing, same schema as v5 |

---

## 7. 注意事项

- **No software installation.** This command does not install the C++ SDK, Visual Studio, Xcode, or any other development toolchain.
- **No Photoshop execution.** The command does not run scripts in Photoshop or launch the UXP Developer Tool.
- **No package management.** `npm install`, `pip install`, or similar dependency installation is not performed.
- **No build execution.** UXP `dist/` remains empty; C++ projects require manual build configuration.
- **Cross-surface hybrid projects** (UXP + C++): Run `/photoshop-create uxp` first, then `/photoshop-create cpp` separately, or manually merge the two structures. Hybrid plugins require matching `component ID` fields between UXP `manifest.json` and the C++ `PSDLLMain()` registration.
- For Marketplace-distributed plugins, the `manifest.json` must ship a single `host` definition, not an array.
