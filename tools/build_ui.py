#!/usr/bin/env python3
"""
customize.sh UI Builder, Live Previewer, Module Packager & update.json Generator
Generates a portrait-safe (<= 56 chars wide) Infinity-X style customize.sh
from module.prop and ui_config.json, simulates narrow-screen terminal output,
packages the flashable ZIP (including action.sh & webroot/), and updates update.json.
"""

import json
import os
import re
import sys
import time
import zipfile

MAX_WIDTH = 56  # Strict limit to prevent wrapping on narrow portrait screens

BLOCK_FONT = {
    "A": [" ███ ", "█   █", "█████", "█   █", "█   █"],
    "B": ["████ ", "█   █", "████ ", "█   █", "████ "],
    "C": [" ████", "█    ", "█    ", "█    ", " ████"],
    "D": ["████ ", "█   █", "█   █", "█   █", "████ "],
    "E": ["█████", "█    ", "████ ", "█    ", "█████"],
    "F": ["█████", "█    ", "████ ", "█    ", "█    "],
    "G": [" ████", "█    ", "█  ██", "█   █", " ████"],
    "H": ["█   █", "█   █", "█████", "█   █", "█   █"],
    "I": ["███", " █ ", " █ ", " █ ", "███"],
    "J": ["  ███", "    █", "    █", "█   █", " ███ "],
    "K": ["█   █", "█  █ ", "███  ", "█  █ ", "█   █"],
    "L": ["█    ", "█    ", "█    ", "█    ", "█████"],
    "M": ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █"],
    "O": [" ███ ", "█   █", "█   █", "█   █", " ███ "],
    "P": ["████ ", "█   █", "████ ", "█    ", "█    "],
    "Q": [" ███ ", "█   █", "█ █ █", "█  ██", " ████"],
    "R": ["████ ", "█   █", "████ ", "█  █ ", "█   █"],
    "S": [" ████", "█    ", " ███ ", "    █", "████ "],
    "T": ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
    "U": ["█   █", "█   █", "█   █", "█   █", " ███ "],
    "V": ["█   █", "█   █", "█   █", " █ █ ", "  █  "],
    "W": ["█   █", "█   █", "█ █ █", "██ ██", "█   █"],
    "X": ["█   █", " █ █ ", "  █  ", " █ █ ", "█   █"],
    "Y": ["█   █", " █ █ ", "  █  ", "  █  ", "  █  "],
    "Z": ["█████", "   █ ", "  █  ", " █   ", "█████"],
    "0": [" ███ ", "█  ██", "█ █ █", "██  █", " ███ "],
    "1": [" ██ ", "███ ", " ██ ", " ██ ", "████"],
    "2": [" ███ ", "█   █", "  ██ ", " █   ", "█████"],
    "3": ["████ ", "    █", " ███ ", "    █", "████ "],
    "4": ["█  █ ", "█  █ ", "█████", "   █ ", "   █ "],
    "5": ["█████", "█    ", "████ ", "    █", "████ "],
    "6": [" ███ ", "█    ", "████ ", "█   █", " ███ "],
    "7": ["█████", "   █ ", "  █  ", " █   ", " █   "],
    "8": [" ███ ", "█   █", " ███ ", "█   █", " ███ "],
    "9": [" ███ ", "█   █", " ████", "    █", " ███ "],
    "-": ["     ", "     ", " ███ ", "     ", "     "],
    "_": ["     ", "     ", "     ", "     ", "█████"],
    "+": ["     ", "  █  ", " ███ ", "  █  ", "     "],
    " ": ["   ", "   ", "   ", "   ", "   "],
}


def parse_module_prop(path="module.prop"):
    props = {}
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
    return props


def sanitize_line(text, max_len=MAX_WIDTH):
    """Strip carriage returns/ANSI codes and enforce narrow-screen width."""
    text = text.replace("\r", "").replace("\n", " ")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text


def render_ascii_banner(title, subtitle=""):
    """Generates a centered block ASCII banner guaranteed <= MAX_WIDTH chars."""
    clean_title = "".join(c if c in BLOCK_FONT else " " for c in title.upper()).strip()
    while clean_title:
        width = sum(len(BLOCK_FONT[c][0]) for c in clean_title) + (len(clean_title) - 1)
        if width <= MAX_WIDTH - 4:
            break
        clean_title = clean_title[:-1]

    lines = ['  ui_print " "']
    if clean_title:
        rows = [" ".join(BLOCK_FONT[c][r] for c in clean_title) for r in range(5)]
        for row in rows:
            centered = row.center(MAX_WIDTH)
            lines.append(f'  ui_print "{sanitize_line(centered)}"')

    if subtitle:
        spaced = " ".join(subtitle.upper())
        tag = f"[ {spaced} ]"
        if len(tag) > MAX_WIDTH - 2:
            tag = f"[ {subtitle.upper()} ]"
        centered_sub = sanitize_line(tag).center(MAX_WIDTH)
        lines.append(f'  ui_print "{centered_sub}"')

    lines.append('  ui_print " "')
    return "\n".join(lines)


def make_progress_bar(percent, width=20):
    filled = round((percent / 100) * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {percent}%"


def generate_customize_sh(props, cfg, out_path="customize.sh"):
    banner_title = cfg.get("banner_title") or props.get("name", "MODULE")
    banner_subtitle = cfg.get("banner_subtitle", "MODULE EDITION")
    sleep_sec = float(cfg.get("stage_sleep", 0.3))
    sleep_sec = max(0.0, min(0.5, sleep_sec))

    divider = "━" * (MAX_WIDTH - 2)
    banner_code = render_ascii_banner(banner_title, banner_subtitle)

    menu = cfg.get("volume_menu", {})
    menu_block = ""
    if menu.get("enabled", False):
        prompt = sanitize_line(menu.get("prompt", "Select Installation Profile:"))
        vol_up = sanitize_line(menu.get("vol_up_label", "Performance Mode"))
        vol_dn = sanitize_line(menu.get("vol_down_label", "Balanced Mode"))
        timeout_s = int(menu.get("timeout", 10))
        menu_block = f"""
# Interactive Volume-Key Menu
twrp_progress 0.25
ui_print "  [?] {prompt}"
ui_print "      [Vol+] {vol_up}"
ui_print "      [Vol-] {vol_dn}"
ui_print " "

if chooseport {timeout_s}; then
  SELECTED_PROFILE="{vol_up}"
  ui_print "  [✓] Selected: {vol_up}"
else
  SELECTED_PROFILE="{vol_dn}"
  ui_print "  [✓] Selected: {vol_dn}"
fi
ui_print " "
"""

    stages = cfg.get(
        "stages",
        [
            {"label": "Extracting module files...", "percent": 35, "cmd": "# Extract step"},
            {"label": "Applying system tweaks...", "percent": 70, "cmd": "# Config step"},
            {"label": "Setting permissions...", "percent": 100, "cmd": 'set_perm_recursive "$MODPATH" 0 0 0755 0644'},
        ],
    )

    stage_blocks = []
    total = len(stages)
    for idx, st in enumerate(stages, start=1):
        pct = int(st.get("percent", round((idx / total) * 100)))
        twrp_frac = f"{pct / 100:.2f}"
        label = sanitize_line(f"[{idx}/{total}] {st.get('label', 'Processing...')}", MAX_WIDTH - 4)
        bar = make_progress_bar(pct, width=20)
        cmd = st.get("cmd", "").strip()
        sleep_line = f"sleep {sleep_sec}" if (sleep_sec > 0 and idx < total) else ""

        block = f"""twrp_progress {twrp_frac}
ui_print "  {label}"
{cmd}
ui_print "  {bar}"
ui_print " "
{sleep_line}"""
        stage_blocks.append(block.strip())

    stages_code = "\n\n".join(stage_blocks)

    script = f"""#!/system/bin/sh
##########################################################################################
# Auto-generated by customize.sh UI Builder (v1.0.0)
# Narrow-screen safe (<={MAX_WIDTH} chars/line) | No carriage returns or clear commands
##########################################################################################

SKIPMOUNT={str(cfg.get("skipmount", False)).lower()}
PROPFILE={str(cfg.get("propfile", False)).lower()}
POSTFSDATA={str(cfg.get("postfsdata", False)).lower()}
LATESTARTSERVICE={str(cfg.get("latestartservice", False)).lower()}

twrp_progress() {{
  if [ "$BOOTMODE" = "false" ] && [ -n "$OUTFD" ]; then
    echo "set_progress $1" >&$OUTFD
  fi
}}

chooseport() {{
  local delay=${{1:-10}}
  while true; do
    local event=$(timeout $delay getevent -lc 1 2>&1 | tr -d '\r')
    case "$event" in
      *KEY_VOLUMEUP*DOWN*) return 0 ;;
      *KEY_VOLUMEDOWN*DOWN*) return 1 ;;
    esac
  done
}}

ui_banner() {{
{banner_code}
}}

MODNAME=$(grep_prop name "$MODPATH/module.prop")
MODVER=$(grep_prop version "$MODPATH/module.prop")
MODAUTH=$(grep_prop author "$MODPATH/module.prop")
DEVICE=$(getprop ro.product.device)
ANDROID=$(getprop ro.build.version.release)

if [ "$KSU" = "true" ]; then
  ROOT_ENV="KernelSU ($KSU_VER)"
elif [ "$APATCH" = "true" ]; then
  ROOT_ENV="APatch ($APATCH_VER)"
elif [ "$BOOTMODE" = "true" ]; then
  ROOT_ENV="Magisk ($MAGISK_VER)"
else
  ROOT_ENV="Custom Recovery"
fi

twrp_progress 0.10
ui_banner

ui_print " {divider}"
ui_print "  • Module  : $MODNAME"
ui_print "  • Version : $MODVER"
ui_print "  • Author  : $MODAUTH"
ui_print "  • Device  : $DEVICE ($ARCH)"
ui_print "  • Android : $ANDROID"
ui_print "  • Manager : $ROOT_ENV"
ui_print " {divider}"
ui_print " "
{menu_block}
{stages_code}

twrp_progress 1.00
ui_print " {divider}"
ui_print "  ✔ Installation Complete!"
ui_print "  ↻ Reboot your device to apply changes."
ui_print " {divider}"
ui_print " "
"""
    script = script.replace("\r\n", "\n")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(script)
    print(f"[✓] Generated {out_path} (Max line width enforced: {MAX_WIDTH} chars)")


def preview_ui(props, script_path="customize.sh", animate=True):
    """Simulates a 58-column portrait Magisk/TWRP console log in your terminal."""
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Missing {script_path}")

    mock_vars = {
        "$MODNAME": props.get("name", "Infinity Tweaks"),
        "$MODVER": props.get("version", "v1.0.0"),
        "$MODAUTH": props.get("author", "YourName"),
        "$DEVICE": "mondrian",
        "$ARCH": "arm64",
        "$ANDROID": "15",
        "$ROOT_ENV": "Magisk (28.1)",
        "$SELECTED_PROFILE": "Performance Mode",
    }

    frame_border = "┌" + ("─" * 58) + "┐"
    frame_footer = "└" + ("─" * 58) + "┘"

    print("\n" + frame_border)
    print("│" + " PORTRAIT LOG PREVIEW (58-COL PHONE SCREEN) ".center(58) + "│")
    print("├" + ("─" * 58) + "┤")

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            m = re.match(r'^ui_print\s+"(.*)"$', stripped)
            if m:
                out = m.group(1)
                for k, v in mock_vars.items():
                    out = out.replace(k, v)
                wrapped = [out[i : i + 58] for i in range(0, max(1, len(out)), 58)]
                for chunk in wrapped:
                    print("│" + chunk.ljust(58) + "│")
            elif animate and stripped.startswith("sleep "):
                try:
                    delay = float(stripped.split()[1])
                    time.sleep(min(delay, 0.5))
                except ValueError:
                    pass

    print(frame_footer + "\n")


def package_zip(props, out_dir="dist"):
    os.makedirs(out_dir, exist_ok=True)
    mod_id = props.get("id", "module")
    mod_ver = props.get("version", "v1.0.0")
    zip_filename = f"{mod_id}-{mod_ver}.zip"
    zip_name = os.path.join(out_dir, zip_filename)

    exclude_dirs = {".git", ".github", "tools", "dist", "__pycache__"}
    exclude_files = {".gitignore", "README.md", "ui_config.json", "update.json", "CHANGELOG.md"}

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in exclude_files or file.endswith(".zip"):
                    continue
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, ".")
                zf.write(full_path, arcname)

    print(f"[✓] Packaged flashable module: {zip_name}")
    return zip_filename


def generate_update_json(props, zip_filename, out_path="update.json"):
    """Generates Magisk/KernelSU/MMRL compatible update.json."""
    repo = os.environ.get("GITHUB_REPOSITORY", "YourUsername/YourRepo")
    mod_ver = props.get("version", "v1.0.0")
    ver_code = int(props.get("versionCode", 100))

    zip_url = f"https://github.com/{repo}/releases/download/{mod_ver}/{zip_filename}"
    changelog_url = f"https://raw.githubusercontent.com/{repo}/main/CHANGELOG.md"

    update_data = {
        "version": mod_ver,
        "versionCode": ver_code,
        "zipUrl": zip_url,
        "changelog": changelog_url,
    }

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(update_data, f, indent=2)
        f.write("\n")

    print(f"[✓] Generated {out_path} -> {zip_url}")


if __name__ == "__main__":
    props = parse_module_prop("module.prop")
    cfg = {}
    if os.path.exists("ui_config.json"):
        with open("ui_config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)

    generate_customize_sh(props, cfg, "customize.sh")

    if "--preview" in sys.argv:
        preview_ui(props, "customize.sh", animate=("--no-sleep" not in sys.argv))

    zip_filename = f"{props.get('id', 'module')}-{props.get('version', 'v1.0.0')}.zip"
    if "--pack" in sys.argv:
        zip_filename = package_zip(props)

    if "--update-json" in sys.argv:
        generate_update_json(props, zip_filename, "update.json")
