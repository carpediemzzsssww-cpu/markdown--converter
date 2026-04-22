"""MD -> standalone HTML via pandoc with inlined CSS + theme override."""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import themes


def convert(src: Path, out: Path, assets_dir: Path, style: dict) -> None:
    css_path = assets_dir / "pdf-styles.css"
    cmd = ["pandoc", str(src), "-o", str(out),
           "--from", "gfm+smart", "--to", "html5",
           "--standalone", "--self-contained",
           "--metadata", f"title={src.stem}"]
    if css_path.exists():
        cmd += ["--css", str(css_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Pandoc 3+: --self-contained renamed to --embed-resources
        if "self-contained" in result.stderr:
            cmd = [c if c != "--self-contained" else "--embed-resources" for c in cmd]
            result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "pandoc 失败")

    # Inject theme override style block at end of <head>
    override = themes.css_override(
        style.get("font", themes.DEFAULTS["font"]),
        style.get("size", themes.DEFAULTS["size"]),
        style.get("color", themes.DEFAULTS["color"]),
        style.get("primary", "zh"),
    )
    html_text = out.read_text(encoding="utf-8")
    inject = f"<style>{override}</style>"
    if "</head>" in html_text:
        html_text = html_text.replace("</head>", inject + "</head>", 1)
    else:
        html_text = inject + html_text
    out.write_text(html_text, encoding="utf-8")
