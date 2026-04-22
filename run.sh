#!/usr/bin/env bash
# Markdown Converter — one-click launcher
set -e

cd "$(dirname "$0")"

# .app / AppleScript launches use a minimal PATH — add brew so pandoc is found
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

echo "→ Markdown Converter"

# 1. Check pandoc
if ! command -v pandoc >/dev/null 2>&1; then
  echo ""
  echo "  ✗ pandoc 未安装"
  echo "  请运行: brew install pandoc"
  echo ""
  exit 1
fi

# 2. venv
if [ ! -d ".venv" ]; then
  echo "  · 首次运行，创建虚拟环境"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Install deps (quiet if already installed)
if [ ! -f ".venv/.deps-installed" ]; then
  echo "  · 安装依赖"
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  touch .venv/.deps-installed
fi

# 4. weasyprint needs Homebrew's libgobject / pango on macOS
if [ -d "/opt/homebrew/lib" ]; then
  export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"
fi

# 5. Launch (forward any argv — used by Finder drop onto the .app icon)
exec python app.py "$@"
