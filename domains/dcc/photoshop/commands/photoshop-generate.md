# `/photoshop-generate` — Photoshop Code Generation

Generates Photoshop ExtendScript/UXP code templates for common operations. Wraps `opencode generate photoshop-*` invocations from 方案.md Section 2.2.

## Usage

```
/photoshop-generate <category> [options]
```

Aliases: `/ps-generate`, `/ps-gen`

---

## Categories

### 1. Layer Operations (`layer` / `layer-op`)

Generate ExtendScript (.jsx) layer manipulation code.

**Options:**
- `--action` (required): comma-separated list of operations

**Supported actions and templates:**

#### `create`
```javascript
// @target photoshop
(function () {
    if (app.documents.length === 0) { alert("No document open."); return; }
    var doc = app.activeDocument;
    var newLayer = doc.artLayers.add();
    newLayer.name = "New Layer";
    // Set properties after creation
    newLayer.opacity = 100;
    newLayer.blendMode = BlendMode.NORMAL;
})();
```

#### `rename`
```javascript
(function () {
    if (app.documents.length === 0) return;
    var doc = app.activeDocument;
    if (doc.activeLayer) {
        doc.activeLayer.name = "RenamedLayer";
    }
})();
```

#### `delete`
```javascript
(function () {
    if (app.documents.length === 0) return;
    var doc = app.activeDocument;
    if (doc.activeLayer && !doc.activeLayer.isBackgroundLayer) {
        doc.activeLayer.remove();
    }
})();
```

#### `duplicate`
```javascript
(function () {
    if (app.documents.length === 0) return;
    var doc = app.activeDocument;
    var dupLayer = doc.activeLayer.duplicate();
    dupLayer.name = doc.activeLayer.name + " copy";
})();
```

#### `group`
```javascript
(function () {
    if (app.documents.length === 0) return;
    var doc = app.activeDocument;
    var layerSet = doc.layerSets.add();
    layerSet.name = "New Group";
    // Move active layer into group
    doc.activeLayer.move(layerSet, ElementPlacement.PLACEATEND);
})();
```

#### `merge`
```javascript
(function () {
    if (app.documents.length === 0) return;
    var doc = app.activeDocument;
    // Merge visible layers (equivalent to Ctrl+Shift+E)
    doc.mergeVisibleLayers();
    // Or merge linked layers: doc.mergeLinkedLayers()
    // Or merge a specific group: layerSet.merged()
})();
```

#### `rasterize`
```javascript
(function () {
    if (app.documents.length === 0) return;
    var doc = app.activeDocument;
    doc.activeLayer.rasterize(RasterizeType.ENTIRELAYER);
})();
```

---

### 2. Batch Processing (`batch`)

Generate ExtendScript (.jsx) for batch file processing across a folder.

**Options:**
- `--input-folder` (required): source directory path
- `--output-format` (required): target format — `jpg`, `png`, `tiff`, `psd`
- `--resize` (optional): target dimensions, e.g. `1920x1080`

**Template:**

```javascript
// @target photoshop
(function () {
    if (app.documents.length > 0) { app.activeDocument.close(SaveOptions.DONOTSAVECHANGES); }

    var inputFolder = Folder("INPUT_FOLDER_PATH_HERE");
    var outputFolder = Folder("OUTPUT_FOLDER_PATH_HERE");
    if (!inputFolder.exists) { alert("Input folder not found."); return; }
    if (!outputFolder.exists) outputFolder.create();

    var fileList = inputFolder.getFiles(/\.(psd|tif|tiff|jpg|jpeg|png)$/i);
    for (var i = 0; i < fileList.length; i++) {
        var doc = app.open(fileList[i]);
        // --- optional resize block ---
        // if (doc.width > 1920) doc.resizeImage(UnitValue(1920, "px"));
        // --- end resize block ---
        var saveFile = new File(outputFolder + "/" + doc.name.replace(/\.\w+$/, ".TARGET_EXT"));
        var saveOpts = getSaveOptions("TARGET_EXT");
        doc.saveAs(saveFile, saveOpts, true, Extension.LOWERCASE);
        doc.close(SaveOptions.DONOTSAVECHANGES);
    }

    function getSaveOptions(ext) {
        ext = ext.toLowerCase();
        if (ext === "jpg" || ext === "jpeg") {
            var opts = new JPEGSaveOptions();
            opts.quality = 12;
            opts.embedColorProfile = true;
            opts.formatOptions = FormatOptions.STANDARDBASELINE;
            return opts;
        }
        if (ext === "png") {
            var opts = new PNGSaveOptions();
            opts.compression = 6;
            opts.interlaced = false;
            return opts;
        }
        if (ext === "tiff" || ext === "tif") {
            var opts = new TiffSaveOptions();
            opts.compression = TIFFEncoding.TIFFLZW;
            opts.alphaChannels = true;
            opts.layers = false;
            opts.imageCompression = MethodType.LZW;
            return opts;
        }
        if (ext === "psd") {
            var opts = new PhotoshopSaveOptions();
            opts.alphaChannels = true;
            opts.layers = true;
            opts.spotColors = true;
            return opts;
        }
        return null;
    }
})();
```

**Format conversion notes:**

| Output Format | SaveOptions Class     | Key Properties                               |
|---------------|-----------------------|----------------------------------------------|
| JPEG          | `JPEGSaveOptions`     | `quality` (0–12), `embedColorProfile`, `matte` |
| PNG           | `PNGSaveOptions`      | `compression` (0–6), `interlaced`             |
| TIFF          | `TiffSaveOptions`     | `compression` (LZW/JPEG/ZIP/None), `layers`   |
| PSD           | `PhotoshopSaveOptions`| `alphaChannels`, `layers`, `spotColors`       |

---

### 3. UXP UI Components (`uxp-ui`)

Generate UXP (.psjs + HTML) UI component stubs for panel plugins.

**Options:**
- `--component` (required): comma-separated list — `button`, `slider`, `color-picker`, `dropdown`, `checkbox`, `text-input`

**General UXP UI structure:**

```html
<!-- index.html — Panel entry point -->
<!DOCTYPE html>
<html>
<head>
<script src="main.psjs"></script>
<style>
  body { font-family: sans-serif; padding: 12px; }
  /* Use Spectrum Web Components design tokens for Adobe-native look:
     https://opensource.adobe.com/spectrum-css/ */
</style>
</head>
<body>
  <!-- Components injected here -->
</body>
</html>
```

```javascript
// main.psjs — Panel logic entry
"use strict";
const app = require('photoshop').app;
const core = require('photoshop').core;
```

**Component stubs:**

#### Button
```javascript
// HTML: <button id="myBtn">Run Action</button>
// .psjs:
document.getElementById("myBtn").addEventListener("click", async function () {
    await core.executeAsModal(async () => {
        const doc = app.activeDocument;
        if (!doc) { app.showAlert("No document open."); return; }
        // ... operation ...
    });
});
```

#### Slider
```javascript
// HTML:
// <label for="opacitySlider">Opacity: <span id="opacityVal">100</span>%</label>
// <input type="range" id="opacitySlider" min="0" max="100" value="100">
// .psjs:
document.getElementById("opacitySlider").addEventListener("input", function (e) {
    document.getElementById("opacityVal").textContent = e.target.value;
});
document.getElementById("applyOpacity").addEventListener("click", async function () {
    var val = parseInt(document.getElementById("opacitySlider").value, 10);
    await core.executeAsModal(async () => {
        if (app.activeDocument) app.activeDocument.activeLayer.opacity = val;
    });
});
```

#### Color Picker
```javascript
// HTML: <input type="color" id="colorPicker" value="#ff0000">
// .psjs:
document.getElementById("colorPicker").addEventListener("input", function (e) {
    var hex = e.target.value; // "#ff0000"
    // Convert hex to RGB for Photoshop API
    var r = parseInt(hex.slice(1,3), 16);
    var g = parseInt(hex.slice(3,5), 16);
    var b = parseInt(hex.slice(5,7), 16);
    // Use with batchPlay() to set foreground color
    // Reference: require('photoshop').action
});
```

#### Dropdown
```javascript
// HTML:
// <select id="blendModeSelect">
//   <option value="normal">Normal</option>
//   <option value="multiply">Multiply</option>
//   <option value="screen">Screen</option>
// </select>
// .psjs:
document.getElementById("blendModeSelect").addEventListener("change", async function (e) {
    var mode = e.target.value;
    await core.executeAsModal(async () => {
        if (app.activeDocument) {
            // BlendMode enum is accessed via app.blendModes or batchPlay
            // ExtendScript: var blendEnum = eval("BlendMode." + mode.toUpperCase());
        }
    });
});
```

#### Checkbox
```javascript
// HTML:
// <label><input type="checkbox" id="visibleCheck" checked> Keep Visible</label>
// .psjs:
document.getElementById("visibleCheck").addEventListener("change", function (e) {
    var isChecked = e.target.checked;
    // Use value in subsequent operations
});
```

#### Text Input
```javascript
// HTML:
// <label>Layer Name: <input type="text" id="layerNameInput" value="New Layer"></label>
// .psjs:
document.getElementById("applyNameBtn").addEventListener("click", async function () {
    var name = document.getElementById("layerNameInput").value;
    if (!name) { app.showAlert("Name cannot be empty."); return; }
    await core.executeAsModal(async () => {
        if (app.activeDocument) app.activeDocument.activeLayer.name = name;
    });
});
```

---

### 4. manifest.json Generation (`manifest`)

Generate UXP `manifest.json` files for v4, v5, or v6.

**Options:**
- `--version` (required): manifest version — `4`, `5`, or `6`
- `--host-min` (required): minimum Photoshop version, e.g. `24.0`
- `--permissions` (optional): comma-separated UXP permissions

**Templates:**

#### v4 (PS 2022–2023, `apiVersion: 2`)
```json
{
    "manifestVersion": 4,
    "id": "com.example.myplugin",
    "version": "1.0.0",
    "name": "My Plugin",
    "entrypoints": [
        {
            "type": "command",
            "id": "run",
            "label": "Run My Plugin"
        }
    ],
    "host": [
        {
            "app": "PS",
            "minVersion": "23.0.0"
        }
    ]
}
```

#### v5 (PS 2023+ — adds `requiredPermissions`)
```json
{
    "manifestVersion": 5,
    "id": "com.example.myplugin",
    "version": "1.0.0",
    "name": "My Plugin",
    "entrypoints": [
        {
            "type": "panel",
            "id": "mainPanel",
            "label": "My Plugin",
            "icons": [
                { "width": 23, "height": 23, "path": "icons/dark.png" },
                { "width": 46, "height": 46, "path": "icons/dark@2x.png" }
            ]
        }
    ],
    "host": [
        {
            "app": "PS",
            "minVersion": "24.0.0"
        }
    ],
    "requiredPermissions": {
        "localFileSystem": "readWrite",
        "network": "disabled",
        "creativeCloud": "disabled"
    }
}
```

#### v6 (PS 2024+ — enhanced permissions model)
```json
{
    "manifestVersion": 6,
    "id": "com.example.myplugin",
    "version": "1.0.0",
    "name": "My Plugin",
    "entrypoints": [
        {
            "type": "panel",
            "id": "mainPanel",
            "label": "My Plugin",
            "icons": [
                { "width": 23, "height": 23, "path": "icons/dark.png" },
                { "width": 46, "height": 46, "path": "icons/dark@2x.png" }
            ]
        }
    ],
    "host": [
        {
            "app": "PS",
            "minVersion": "25.0.0"
        }
    ],
    "requiredPermissions": {
        "localFileSystem": "readWrite",
        "network": "disabled",
        "creativeCloud": "disabled",
        "clipboard": "readWrite",
        "openWithDefaultApp": "enabled"
    },
    "features": {
        "webview": "enabled"
    }
}
```

**Permission reference:**

| Permission              | Values                    | Description                          |
|-------------------------|---------------------------|--------------------------------------|
| `localFileSystem`       | `none`, `read`, `readWrite`| File open/save dialogs, folder access |
| `network`               | `none`, `enabled`, `disabled`| HTTP/HTTPS requests                  |
| `creativeCloud`         | `none`, `enabled`, `disabled`| CC library access                    |
| `clipboard`             | `none`, `readWrite`       | System clipboard (v6+)               |
| `openWithDefaultApp`    | `none`, `enabled`         | Open files in OS default app (v6+)   |

---

### 5. `.atn` to ExtendScript Conversion (`atn` / `action-to-script`)

Generate guidance for converting Photoshop Action (.atn) files to ExtendScript (.jsx).

**Options:**
- `--input` (required): path to `.atn` file

**Important: `.atn` is a binary format** — this command does NOT parse `.atn` files directly. Instead, it provides the recommended workflow and code scaffolding.

**Conversion workflow:**

1. **Load the Action in Photoshop** — File > Open or double-click the `.atn`
2. **Open the Actions panel** (Window > Actions)
3. **Select the action** and click the panel menu > **"Batch Playback Settings..."**
4. **Record as Script** using the Scripting Listener plugin (Adobe's official logging plug-in):
   - Install Scripting Listener from Adobe's developer resources
   - Enable via Photoshop menu: Plugins > Scripting Listener > Enable Logging
   - Play the action once — the listener outputs JavaScript equivalents to the ESTK Console
5. **Extract the output** and wrap in an ExtendScript function:

```javascript
// @target photoshop
(function () {
    // Paste listener output here — typically a series of
    // executeAction() calls with descriptor objects.
    // Example structure (not a real action):
    try {
        var desc = new ActionDescriptor();
        var ref = new ActionReference();
        ref.putEnumerated(charIDToTypeID("Lyr "), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
        desc.putReference(charIDToTypeID("null"), ref);
        executeAction(charIDToTypeID("Mk  "), desc, DialogModes.NO);
    } catch (e) {
        alert("Action step failed: " + e.toString());
    }
})();
```

**Key conversion patterns:**

| Action Panel Step       | ExtendScript Equivalent                        |
|-------------------------|------------------------------------------------|
| New Layer               | `app.activeDocument.artLayers.add()`           |
| Set Foreground Color    | `app.foregroundColor.rgb = [R, G, B]`          |
| Fill Selection          | `app.activeDocument.selection.fill(fillColor)`  |
| Apply Filter            | `app.activeDocument.activeLayer.applyFilter()` |
| Save Document           | `app.activeDocument.saveAs()` / `save()`       |
| Close Document          | `app.activeDocument.close(SaveOptions.xxxxx)`  |
| Select Layer by Name    | `app.activeDocument.layers.getByName("name")`  |
| Resize Image            | `app.activeDocument.resizeImage()`              |

**Limitations of automatic .atn parsing:**
- `.atn` stores serialized `PIActionDescriptor` data — it is a proprietary binary format with no published public schema
- Action steps can contain conditional logic (if/else branches) that are not exposed to the Scripting Listener
- Action sets with multiple child actions require manual disambiguation
- Some action steps (e.g., modal dialogs) produce no listener output — these need manual implementation
- Character encoding in action names varies between Photoshop versions

> **Recommendation**: For complex actions, record each step individually using Scripting Listener rather than attempting batch conversion. For simple linear actions, manual transcription from the listener log is reliable.

---

## Version Map

| Generation Category     | ExtendScript | UXP (.psjs) | Notes                              |
|-------------------------|:---:|:---:|------------------------------------|
| Layer Operations        |  ✓  |  ✓  | UXP needs `executeAsModal` wrapper |
| Batch Processing        |  ✓  |  —  | Use ExtendScript for headless batch |
| UXP UI Components       |  —  |  ✓  | HTML panel structure required      |
| Manifest Generation     |  —  |  ✓  | JSON config, no runtime code       |
| .atn Conversion Guidance|  ✓  |  —  | Workflow guidance only             |

---

## References

- Adobe Photoshop JavaScript Reference (ExtendScript DOM)
- Adobe UXP Developer Guide (manifest versions, permissions)
- Photoshop Scripting Listener plug-in (Adobe developer download)
- 方案.md Section 2.2 — Code Generation architecture
