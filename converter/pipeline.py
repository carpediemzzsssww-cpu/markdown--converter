"""Conversion pipeline — routes a single .md file to the right converter."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

from . import docx as docx_mod
from . import pdf as pdf_mod
from . import xlsx as xlsx_mod
from . import html as html_mod
from . import themes

_CONVERTERS = {
    "docx": docx_mod.convert,
    "pdf": pdf_mod.convert,
    "xlsx": xlsx_mod.convert,
    "html": html_mod.convert,
}


def resolve_output_path(src: Path, out_dir: Path, target_fmt: str) -> Path:
    """Build the output path, adding a timestamp if a file with the same name exists."""
    out_dir.mkdir(parents=True, exist_ok=True)
    base = src.stem
    candidate = out_dir / f"{base}.{target_fmt}"
    if candidate.exists():
        stamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        candidate = out_dir / f"{base}_{stamp}.{target_fmt}"
    return candidate


def convert(src_path: str, target_fmt: str, out_dir: Path, assets_dir: Path,
            style: dict | None = None) -> dict:
    """Convert a single .md file. Returns {ok, output, error}.

    `style` is a dict with keys {font, size, color, lang}. `lang` is auto/zh/en.
    The pipeline resolves it to the concrete primary ('zh'|'en') and passes that
    along as `primary` inside the style forwarded to each converter.
    """
    target_fmt = target_fmt.lower()
    if target_fmt not in _CONVERTERS:
        return {"ok": False, "error": f"不支持的格式: {target_fmt}"}

    src = Path(src_path).expanduser().resolve()
    if not src.exists():
        return {"ok": False, "error": "文件不存在"}
    if src.suffix.lower() not in (".md", ".markdown"):
        return {"ok": False, "error": "只支持 .md / .markdown"}

    style = dict(style or {})
    try:
        md_text = src.read_text(encoding="utf-8")
    except Exception:
        md_text = ""
    style["primary"] = themes.resolve_lang(style.get("lang", themes.DEFAULTS["lang"]), md_text)

    output = resolve_output_path(src, out_dir, target_fmt)

    try:
        _CONVERTERS[target_fmt](src, output, assets_dir, style)
        return {"ok": True, "output": str(output)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
