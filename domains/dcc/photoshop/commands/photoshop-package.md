## `/photoshop-package` — Package & Publish Photoshop Plugins

**Operational guidance command** for packaging UXP plugins into `.zxp` archives, applying digital signatures, preparing Adobe Creative Cloud Marketplace submission materials, and cleaning up project build artifacts.

> **Capability statement**: This is an operational guide, not automated packaging. All commands provide step-by-step instructions for the AI agent to follow — they do not invoke build tools, execute signing operations, or submit to Adobe Marketplace. The agent acts as a guided assistant walking the developer through each procedure.

---

### 1. Build — Package UXP Plugin as .ZXP

Package a UXP plugin project into a distributable `.zxp` archive using the UXP Developer Tool (UDT).

**Prerequisites:**
- UXP Developer Tool installed ([Adobe Console](https://console.adobe.io/))
- Plugin `manifest.json` passes UDT validation
- Plugin source built into `dist/` (or equivalent output directory)
- Target Photoshop version specified in manifest `host.minVersion`

**Procedure — UDT GUI:**
1. Open UXP Developer Tool
2. Click **Add Plugin** → select your plugin's `manifest.json`
3. Click **Validate** — confirm zero errors; address any warnings
4. Click **Package** → choose output path and filename (e.g., `LayerManager.zxp`)
5. UDT generates `.zxp` archive containing `manifest.json`, `index.html`, all JS bundles, and assets referenced in manifest

**Procedure — UDT CLI (if available):**
```bash
# Locate UDT CLI (platform-dependent):
# macOS: /Applications/UXP Developer Tool.app/Contents/MacOS/UXP Developer Tool
# Windows: C:\Program Files\Adobe\Adobe UXP Developer Tool\UXP Developer Tool.exe

# UDT CLI packaging syntax:
uxp package --input ./path/to/plugin --output ./dist/MyPlugin.zxp
```

**Verification:**
- `.zxp` is a standard ZIP archive — verify contents:
  ```bash
  unzip -l MyPlugin.zxp
  ```
- Confirm the archive contains:
  - `manifest.json` at root
  - `index.html` (or entry point specified in manifest)
  - All referenced scripts, stylesheets, and assets
  - Icon PNGs at `icons/` subdirectory if panel plugin
- Re-validate extracted `manifest.json` by dragging into UDT

**Troubleshooting:**
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Validation fails on `requiredPermissions` | Manifest v5+ missing permissions block | Add `"requiredPermissions"` array |
| Missing assets at runtime | Package excludes files not in manifest | Add asset paths to manifest `"resources"` |
| Icons not appearing | Wrong icon path or size | Place PNGs at `icons/23x23.png`, `icons/46x46.png` |

---

### 2. Sign — Apply Digital Signature to .ZXP

Apply a digital signature to the packaged `.zxp` so Adobe Creative Cloud trusts the plugin and does not display security warnings during installation.

**Self-Signed Certificate (Development / Internal Testing):**

> **DO NOT** create, store, or transmit actual certificates. Guide the developer through these steps verbally — do not generate certs or keystores programmatically.

```
Step-by-step instructions for the developer:

1. Open terminal / command prompt
2. Generate a self-signed certificate with Adobe-compatible extended key usage:

   macOS / Linux:
   openssl req -x509 -newkey rsa:2048 -keyout mykey.pem -out mycert.pem \
     -days 365 -nodes -subj "/CN=My Company Name/O=My Organization/C=US" \
     -addext "extendedKeyUsage=codeSigning"

   Windows (PowerShell):
   New-SelfSignedCertificate -Type CodeSigning -Subject "CN=My Company Name" \
     -CertStoreLocation Cert:\CurrentUser\My

3. Export the certificate as PKCS#12 (.p12):
   macOS / Linux:
   openssl pkcs12 -export -in mycert.pem -inkey mykey.pem \
     -out my-signing-cert.p12 -passout pass:

   Windows:
   Export-PfxCertificate -Cert Cert:\CurrentUser\My\<Thumbprint> \
     -FilePath my-signing-cert.p12 -Password (ConvertTo-SecureString "" -AsPlainText -Force)

4. Sign the .zxp using the UXP Developer Tool:
   - Open UDT → select plugin → click Package → in signing step, browse to .p12
   - OR use the OS signing tool if available
```

**Adobe Official Signing (Marketplace Distribution):**

> **DO NOT** handle Adobe Marketplace account operations. Only guide the developer to the official Adobe process.

```
1. Enroll in the Adobe Creative Cloud Marketplace Publisher program:
   https://developer.adobe.com/console/

2. Submit plugin for review via Publisher Console:
   - Upload unsigned .zxp to Publisher Console
   - Adobe signs the plugin after approval
   - Signed .zxp is returned for distribution

3. Alternatively, obtain an Adobe-issued code signing certificate:
   - Request via Adobe Developer Console
   - Certificate is managed by Adobe; no local cert storage needed
   - Sign via UDT using Adobe-provided credentials
```

**Verify Signature:**
```bash
# Check if .zxp is signed (extract META-INF directory):
unzip -l MyPlugin.zxp | grep META-INF
# Signed archives contain META-INF/MANIFEST.MF and META-INF/*.SF or *.RSA
```

**Important Security Notes:**
- Store private keys securely — lost keys cannot be recovered
- Expired certificates require re-signing and re-submission
- Adobe may revoke certificates for policy violations; do not sign untrusted code
- Self-signed certificates work for local development but trigger security warnings on other machines

---

### 3. Marketplace Prep — Prepare Adobe Creative Cloud Marketplace Submission

Prepare all materials required for submitting a plugin to the [Adobe Creative Cloud Marketplace](https://exchange.adobe.com/).

**Required Assets:**

| Asset | Specification | Format | Quantity |
|-------|--------------|--------|----------|
| Plugin Icon (small) | 23×23 px, transparent background | PNG | 2 (dark + light theme) |
| Plugin Icon (large) | 46×46 px, transparent background | PNG | 2 (dark + light theme) |
| Feature Graphic | 1024×512 px or 1200×627 px | PNG / JPG | 1 |
| Screenshots | 1920×1080 or 1280×720 px, show key features | PNG / JPG | 3–5 |
| Demo Video (optional) | MP4, H.264, ≤ 60s, show workflow | MP4 | 1 |
| Privacy Policy URL | Link to privacy policy | URL | 1 |

**Icon Generation Guidelines:**
```bash
# If the developer provides a source SVG/PNG, generate all required sizes:
# 23×23 dark theme icon
convert source-icon.png -resize 23x23 icons/23x23-dark.png
# 46×46 dark theme icon
convert source-icon.png -resize 46x46 icons/46x46-dark.png
# Light theme variants (invert or lighten if needed)
convert source-icon.png -resize 23x23 -negate icons/23x23-light.png
convert source-icon.png -resize 46x46 -negate icons/46x46-light.png

# Note: Use ImageMagick or Photoshop itself for generation
```

**Description Template:**
```
Plugin Name: {name}
Version: {version}
Category: {category — e.g., "Design Tools", "Productivity", "Photography"}

## Overview
{2–3 sentence summary of what the plugin does}

## Key Features
- {feature 1}
- {feature 2}
- {feature 3}

## How to Use
{step-by-step usage instructions, 3–5 steps}

## Requirements
- Adobe Photoshop {minVersion} or later
- {Any additional requirements}

## Version History
- {version}: {release notes}

## Support
{Support contact or URL}
```

**Marketplace Submission Checklist:**
- [ ] Plugin successfully packages as `.zxp`
- [ ] `manifest.json` contains single `host` definition (not array) — required by Marketplace
- [ ] All permissions in `requiredPermissions` are minimal and justified
- [ ] Plugin icons for both themes at 23×23 and 46×46
- [ ] Feature graphic meets size requirements
- [ ] 3–5 screenshots showing key functionality
- [ ] Description written in English (or target locale)
- [ ] Privacy policy URL provided (if plugin collects data)
- [ ] Version number matches both manifest and tag
- [ ] Plugin tested on minimum supported Photoshop version
- [ ] Plugin tested on latest Photoshop version

**Submission Process (guide only — do not execute):**
```
1. Log in to https://developer.adobe.com/console/
2. Navigate to "Creative Cloud Publishing" → "Add New Plugin"
3. Fill in plugin details (name, description, category, price tier)
4. Upload plugin icon set and feature graphic
5. Upload 3–5 screenshots
6. Upload the signed .zxp file
7. Complete marketing questionnaire (target audience, use cases)
8. Submit for review (review cycle: 5–10 business days)
9. Monitor submission status in Publisher Console
10. Address any review feedback and resubmit as needed
```

**Common Rejection Reasons:**
- Missing or incorrect icon sizes
- Plugin fails to load in review environment
- Insufficient permissions documentation
- Incomplete or misleading description
- Missing privacy policy (data-collecting plugins)
- Manifest contains multiple `host` definitions

---

### 4. Clean — Remove Build Artifacts and Temporary Files

Clean up project directory by removing build artifacts, temporary files, and development-only files that should not be distributed.

**Files to Remove:**
| Pattern | Reason | Examples |
|---------|--------|---------|
| `dist/` | Built output (regenerated during packaging) | Bundled JS, CSS |
| `node_modules/` | npm dependencies (not included in .zxp) | React, webpack |
| `.git/` | Version control metadata | Git history |
| `*.log` | Build logs, debug logs | `npm-debug.log*` |
| `.temp/`, `tmp/` | Temporary build artifacts | Cached files |
| `*.p12`, `*.pem`, `*.key` | Certificate files (never distribute) | Signing keys |
| `.DS_Store` | macOS directory metadata | — |
| `Thumbs.db` | Windows thumbnail cache | — |
| `*.map` | Source maps (debug only) | Webpack source maps |
| `.env`, `.env.local` | Environment variables, secrets | API keys |
| `test/`, `__tests__/` | Test files (not for distribution) | Unit tests |

**Cleanup Procedure:**
```bash
# Project root cleanup
rm -rf dist/
rm -rf node_modules/
rm -rf .temp/
rm -f *.log
rm -f *.p12 *.pem *.key
rm -f .DS_Store Thumbs.db
rm -f *.map

# Verify no sensitive files remain
find . -name "*.p12" -o -name "*.pem" -o -name "*.key" -o -name ".env*" 2>/dev/null
# Should return no results
```

**Pre-package Cleanup Checklist:**
- [ ] `node_modules/` removed (dependencies bundled by webpack/rollup into dist/)
- [ ] Source maps removed from production bundle
- [ ] No `.env` files with API keys present
- [ ] Certificate files removed from project tree
- [ ] Test files excluded from packaging
- [ ] `dist/` contains only what is referenced in `manifest.json`

**Git Clean (if using git):**
```bash
# Check what would be removed by .gitignore rules
git clean --dry-run -fd

# After review, remove untracked files
git clean -fd
```

---

### Appendix: Quick Reference Card

| Task | Tool | Key Command / Action |
|------|------|---------------------|
| Validate manifest | UDT | Add Plugin → Validate |
| Package .zxp | UDT | Package → select output path |
| Self-sign .zxp | UDT + OpenSSL | Sign with .p12 during packaging step |
| Adobe sign .zxp | Adobe Publisher Console | Submit unsigned .zxp for Adobe signing |
| Generate icons | ImageMagick / Photoshop | Resize source to 23px, 46px |
| Clean project | Shell | `rm -rf dist/ node_modules/ .temp/` |
| Verify archive | Shell | `unzip -l MyPlugin.zxp` |

---

**Related commands:** `/photoshop-create` (project scaffold), `/photoshop-debug` (UXP debugging), `/photoshop-validate` (manifest verification)

**See also:** [Adobe UXP Developer Tool Documentation](https://developer.adobe.com/uxp/), [Creative Cloud Marketplace Publisher Guide](https://developer.adobe.com/console/)
