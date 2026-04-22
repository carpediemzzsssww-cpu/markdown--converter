#!/usr/bin/env bash
# Package Markdown Converter as a clickable .app (AppleScript wrapper)
# After this finishes, drag "Markdown Converter.app" into /Applications.
#
# The generated .app supports:
#   - Double-click to launch
#   - Drop .md files onto its Dock/Applications icon → opens with those files
set -e

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
APP_NAME="Markdown Converter"
OUT="$PROJECT_DIR/$APP_NAME.app"

if [ -d "$OUT" ]; then
  echo "  · 删除旧的 $APP_NAME.app"
  rm -rf "$OUT"
fi

# Generate the AppleScript source. It supports both plain launch and the macOS
# "open with" event (Finder drop onto the .app icon).
SCRIPT=$(cat <<APPLESCRIPT
on run
  do shell script "cd $(printf %q "$PROJECT_DIR") && ./run.sh > /tmp/md-converter.log 2>&1 &"
end run

on open theFiles
  set pathArgs to ""
  repeat with f in theFiles
    set pathArgs to pathArgs & " " & quoted form of POSIX path of f
  end repeat
  do shell script "cd $(printf %q "$PROJECT_DIR") && ./run.sh" & pathArgs & " > /tmp/md-converter.log 2>&1 &"
end open
APPLESCRIPT
)

echo "  · 生成 $APP_NAME.app"
osacompile -o "$OUT" -e "$SCRIPT"

# -------- Custom icon --------
ICON_PNG="$PROJECT_DIR/assets/icon.png"
if [ -f "$ICON_PNG" ]; then
  echo "  · 打包自定义图标"
  ICONSET="$PROJECT_DIR/assets/.build-iconset.iconset"
  rm -rf "$ICONSET" && mkdir -p "$ICONSET"
  # Apple requires multiple sizes inside .iconset then iconutil to pack
  for pair in "16 16" "32 16@2x" "32 32" "64 32@2x" "128 128" "256 128@2x" "256 256" "512 256@2x" "512 512" "1024 512@2x"; do
    set -- $pair
    sz=$1; name=$2
    sips -z "$sz" "$sz" "$ICON_PNG" --out "$ICONSET/icon_${name}.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o "$OUT/Contents/Resources/app.icns" 2>/dev/null || true
  rm -rf "$ICONSET"
fi

# Patch Info.plist to declare support for .md / .markdown files so Finder lets
# users drop them onto the .app icon.
PLIST="$OUT/Contents/Info.plist"
if [ -f "$PLIST" ]; then
  # point CFBundleIconFile at our custom icon (AppleScript .apps default to applet.icns)
  if [ -f "$OUT/Contents/Resources/app.icns" ]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile app" "$PLIST" 2>/dev/null \
      || /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string app" "$PLIST"
    rm -f "$OUT/Contents/Resources/applet.icns"
  fi

  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes array" "$PLIST" 2>/dev/null || true
  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0 dict" "$PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string 'Markdown Document'" "$PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string 'Editor'" "$PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSHandlerRank string 'Alternate'" "$PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes array" "$PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes:0 string 'net.daringfireball.markdown'" "$PLIST"
  /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes:1 string 'public.plain-text'" "$PLIST"
fi

# Re-sign after Info.plist edits (ad-hoc).
codesign --force --deep --sign - "$OUT" 2>/dev/null || true

echo ""
echo "✓ 完成。现在："
echo "  1. 打开 Finder → $PROJECT_DIR"
echo "  2. 把 '$APP_NAME.app' 拖到 /Applications（然后拖到 Dock）"
echo "  3. 双击启动；或把 .md 文件拖到 Dock 的图标上启动"
echo "  4. Spotlight（⌘+空格）搜 'Markdown Converter' 也能启动"
echo ""
