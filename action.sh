#!/system/bin/sh
##########################################################################################
# Magisk / KernelSU / APatch Action Button Script (action.sh)
# Triggered when tapping the "Action / Play" button on the module card
##########################################################################################

MODDIR=${0%/*}
PROPFILE="$MODDIR/module.prop"
STATE_FILE="$MODDIR/.profile_state"

current_state="Balanced"
[ -f "$STATE_FILE" ] && current_state=$(cat "$STATE_FILE")

if [ "$current_state" = "Balanced" ]; then
  new_state="Performance"
else
  new_state="Balanced"
fi

echo "$new_state" > "$STATE_FILE"

# Dynamically update module.prop description so status appears on the module card
sed -i "s/^description=.*/description=[Active: $new_state] Custom system optimizations with Infinity X UI./" "$PROPFILE"

echo "========================================"
echo " Switched profile to: $new_state Mode"
echo "========================================"
