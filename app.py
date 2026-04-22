"""Markdown Converter — PyWebView entry point."""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from pathlib import Path

# Ensure weasyprint can find Homebrew's native libs (pango / glib) on macOS.
if sys.platform == "darwin" and os.path.isdir("/opt/homebrew/lib"):
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
        "/opt/homebrew/lib" + (":" + os.environ["DYLD_FALLBACK_LIBRARY_PATH"]
        if os.environ.get("DYLD_FALLBACK_LIBRARY_PATH") else "")
    )

import webview

from converter import pipeline, themes

ROOT = Path(__file__).parent
UI_DIR = ROOT / "ui"
ASSETS_DIR = ROOT / "assets"
CONFIG_DIR = Path.home() / ".md-converter"
CONFIG_PATH = CONFIG_DIR / "config.json"
STAGING_DIR = CONFIG_DIR / "staging"
DESKTOP_OUT = Path.home() / "Desktop" / "Converted"


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


class Api:
    def __init__(self, initial_files: list[str] | None = None) -> None:
        self.config = _load_config()
        self._last_output_dir: Path | None = None
        self._initial_files: list[str] = list(initial_files or [])

    # ---------- Config ----------
    def get_config(self) -> dict:
        return {
            "output_mode": self.config.get("output_mode", "sibling"),
            "font": self.config.get("font", themes.DEFAULTS["font"]),
            "size": self.config.get("size", themes.DEFAULTS["size"]),
            "color": self.config.get("color", themes.DEFAULTS["color"]),
            "lang": self.config.get("lang", themes.DEFAULTS["lang"]),
        }

    def get_initial_files(self) -> list[str]:
        """Files passed via macOS open event (Finder drag to .app icon). One-shot."""
        files = self._initial_files
        self._initial_files = []
        return files

    def set_output_mode(self, mode: str) -> None:
        if mode in ("sibling", "desktop", "ask"):
            self.config["output_mode"] = mode
            _save_config(self.config)

    def set_dock_badge(self, text: str) -> None:
        """Set the Dock badge label (macOS only). Empty string clears it."""
        if sys.platform != "darwin":
            return
        try:
            from AppKit import NSApp  # type: ignore[import-not-found]
            tile = NSApp.dockTile()
            tile.setBadgeLabel_(text or "")
            tile.display()
        except Exception:
            pass  # pyobjc missing or not a cocoa context — fail silently

    def set_style(self, font: str, size: str, color: str, lang: str = "auto") -> None:
        if font in themes.FONTS:
            self.config["font"] = font
        if size in themes.SIZES:
            self.config["size"] = size
        if color in themes.COLORS:
            self.config["color"] = color
        if lang in ("auto", "zh", "en"):
            self.config["lang"] = lang
        _save_config(self.config)

    def list_presets(self) -> dict:
        """Return labeled presets for the UI dropdowns."""
        return {
            "fonts": [{"id": k, "label": v["label"]} for k, v in themes.FONTS.items()],
            "sizes": [{"id": k, "label": v["label"]} for k, v in themes.SIZES.items()],
            "colors": [{"id": k, "label": v["label"], "swatch": "#" + v["heading"],
                        "accent": "#" + v["accent"]} for k, v in themes.COLORS.items()],
            "langs": themes.LANGS,
        }

    def describe_output_path(self) -> str:
        mode = self.config.get("output_mode", "sibling")
        if mode == "sibling":
            return "源文件旁 ./converted/"
        if mode == "desktop":
            return str(DESKTOP_OUT).replace(str(Path.home()), "~")
        return "每次询问"

    # ---------- Pick & resolve ----------
    def pick_files(self) -> list[str]:
        result = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True,
            file_types=("Markdown files (*.md;*.markdown)", "All files (*.*)"),
        )
        return list(result) if result else []

    def filter_md(self, paths: list[str]) -> list[str]:
        out = []
        for p in paths:
            pp = Path(p).expanduser()
            if pp.is_dir():
                out.extend(str(f) for f in pp.rglob("*.md"))
                out.extend(str(f) for f in pp.rglob("*.markdown"))
            elif pp.suffix.lower() in (".md", ".markdown"):
                out.append(str(pp))
        return out

    def stage_dropped(self, name: str, b64: str) -> str | None:
        """Receive a file dragged into the webview — decode, write to staging, return the path."""
        import base64, re
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        # sanitize filename (strip path separators, leave unicode alone)
        safe = re.sub(r"[/\\\x00]", "_", name).strip() or "dropped.md"
        if not safe.lower().endswith((".md", ".markdown")):
            return None
        dest = STAGING_DIR / safe
        # avoid overwriting previous staged files
        i = 1
        while dest.exists():
            dest = STAGING_DIR / f"{Path(safe).stem}_{i}{Path(safe).suffix}"
            i += 1
        try:
            raw = base64.b64decode(b64)
        except Exception:
            return None
        dest.write_bytes(raw)
        return str(dest)

    def resolve_paths(self, raw: str) -> list[str]:
        """Expand ~, globs, and directory inputs into a flat list of md files."""
        raw = raw.strip().strip('"').strip("'")
        expanded = os.path.expanduser(raw)
        matches = glob.glob(expanded)
        if not matches and Path(expanded).exists():
            matches = [expanded]
        return self.filter_md(matches)

    # ---------- Output dir resolution ----------
    def _output_dir_for(self, src: Path) -> Path | None:
        mode = self.config.get("output_mode", "sibling")
        # dragged-in files live in the staging dir; "sibling" makes no sense there
        is_staged = STAGING_DIR in src.parents
        if mode == "sibling":
            if is_staged:
                return DESKTOP_OUT
            return src.parent / "converted"
        if mode == "desktop":
            return DESKTOP_OUT
        if mode == "ask":
            picked = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
            if not picked:
                return None
            return Path(picked[0])
        return src.parent / "converted"

    # ---------- Preview ----------
    def preview_output_for(self, src_path: str) -> str:
        """Return a human-readable string of where this file will be written."""
        mode = self.config.get("output_mode", "sibling")
        if mode == "ask":
            return "转换时选择"
        try:
            src = Path(src_path).expanduser().resolve()
        except Exception:
            return "—"
        out = self._output_dir_for(src)
        if out is None:
            return "—"
        home = str(Path.home())
        pretty = str(out).replace(home, "~", 1)
        if STAGING_DIR in src.parents and mode == "sibling":
            return f"{pretty}（拖入文件无源路径）"
        return pretty

    # ---------- Convert ----------
    def convert_one(self, src_path: str, target_fmt: str) -> dict:
        src = Path(src_path).expanduser()
        out_dir = self._output_dir_for(src)
        if out_dir is None:
            return {"ok": False, "error": "未选择输出文件夹"}
        style = {
            "font": self.config.get("font", themes.DEFAULTS["font"]),
            "size": self.config.get("size", themes.DEFAULTS["size"]),
            "color": self.config.get("color", themes.DEFAULTS["color"]),
            "lang": self.config.get("lang", themes.DEFAULTS["lang"]),
        }
        res = pipeline.convert(str(src), target_fmt, out_dir, ASSETS_DIR, style)
        if res.get("ok"):
            self._last_output_dir = Path(res["output"]).parent
        return res

    # ---------- Open / reveal ----------
    def open_path(self, path: str) -> None:
        if sys.platform == "darwin":
            subprocess.run(["open", path])
        elif sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path])

    def reveal_path(self, path: str) -> None:
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", path])
        else:
            parent = str(Path(path).parent)
            self.open_path(parent)

    def open_output_dir(self) -> None:
        if self._last_output_dir and self._last_output_dir.exists():
            self.open_path(str(self._last_output_dir))
            return
        mode = self.config.get("output_mode", "sibling")
        if mode == "desktop":
            DESKTOP_OUT.mkdir(parents=True, exist_ok=True)
            self.open_path(str(DESKTOP_OUT))


def _collect_initial_files() -> list[str]:
    """Pick out .md / .markdown paths from sys.argv (passed by macOS open event)."""
    out: list[str] = []
    for a in sys.argv[1:]:
        try:
            p = Path(a).expanduser()
        except Exception:
            continue
        if not p.exists():
            continue
        if p.is_dir():
            out.extend(str(x) for x in p.rglob("*.md"))
            out.extend(str(x) for x in p.rglob("*.markdown"))
        elif p.suffix.lower() in (".md", ".markdown"):
            out.append(str(p.resolve()))
    return out


def main() -> None:
    initial = _collect_initial_files()
    api = Api(initial_files=initial)
    webview.create_window(
        "Markdown Converter",
        str(UI_DIR / "index.html"),
        js_api=api,
        width=900,
        height=720,
        min_size=(720, 560),
        background_color="#F7F2E9",
    )
    webview.start()


if __name__ == "__main__":
    main()
