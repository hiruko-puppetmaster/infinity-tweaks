# Magisk / KernelSU / APatch Module Starter Kit (`v1.0.0`)

All-in-one root module repository template featuring an **Infinity X style `customize.sh` UI generator**, **live 58-column phone screen previewer**, **`action.sh` card button**, **`webroot/` WebUI dashboard**, and **GitHub Actions auto-release & `update.json` builder**.

## Repository Structure
```text
├── .github/workflows/build.yml   # GitHub Actions CI auto-builder, previewer & release workflow
├── tools/build_ui.py             # Python ASCII banner, customize.sh, preview & update.json tool
├── ui_config.json                # Customize banner title, volume menu & install stages here
├── module.prop                   # Module metadata (update updateJson URL with your repo)
├── action.sh                     # Root manager "Action / Play" button script
├── webroot/index.html            # KernelSU / APatch / MMRL WebUI X interactive dashboard
├── update.json                   # Auto-updated JSON endpoint for in-app updates
├── CHANGELOG.md                  # Release notes shown inside root manager update prompts
└── system/                       # Place your module overlay files here
```

## Quick Commands
* **Generate `customize.sh` & preview it in a simulated 58-col phone log:**
  ```bash
  python3 tools/build_ui.py --preview
  ```
* **Build flashable ZIP & `update.json`:**
  ```bash
  python3 tools/build_ui.py --pack --update-json
  ```

## Enforced Narrow-Screen Design Rules
1. **Strict `<= 56` Character Line Limit:** Automatically scales or trims ASCII block banners and truncates long labels so lines never wrap on 58–62 column portrait screens.
2. **Controlled Stage Pauses (`0.3s`):** Clamps `stage_sleep` between `0.0` and `0.5` seconds so progress bars feel responsive without slowing down flashing.
3. **Zero Carriage Returns (`\r`) or `clear`:** Sanitizes all strings and enforces `LF` line endings because TWRP, Magisk, KernelSU, and APatch append each `ui_print` on a new line.
