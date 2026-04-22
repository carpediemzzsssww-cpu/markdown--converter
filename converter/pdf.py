"""MD -> PDF via pandoc (to HTML) -> weasyprint."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from . import themes


def convert(src: Path, out: Path, assets_dir: Path, style: dict) -> None:
    # Step 1: md -> html via pandoc
    result = subprocess.run(
        ["pandoc", str(src), "--from", "gfm+smart", "--to", "html5", "--no-highlight"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pandoc 失败")
    body_html = result.stdout

    # Step 2: wrap in template
    tmpl_path = assets_dir / "html-template.html"
    css_path = assets_dir / "pdf-styles.css"
    title = src.stem

    if tmpl_path.exists():
        tmpl = tmpl_path.read_text(encoding="utf-8")
    else:
        tmpl = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>{{title}}</title></head><body>{{body}}</body></html>"
    full_html = tmpl.replace("{{title}}", title).replace("{{body}}", body_html)

    # Step 3: weasyprint -> pdf
    try:
        from weasyprint import HTML, CSS
    except ImportError as e:
        raise RuntimeError("weasyprint 未安装，请运行 pip install weasyprint") from e

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(full_html)
        tmp_html = f.name

    stylesheets = []
    if css_path.exists():
        stylesheets.append(CSS(filename=str(css_path)))
    # theme override comes last so it wins cascade order
    override = themes.css_override(
        style.get("font", themes.DEFAULTS["font"]),
        style.get("size", themes.DEFAULTS["size"]),
        style.get("color", themes.DEFAULTS["color"]),
        style.get("primary", "zh"),
    )
    stylesheets.append(CSS(string=override))

    HTML(filename=tmp_html, base_url=str(assets_dir)).write_pdf(str(out), stylesheets=stylesheets)

    Path(tmp_html).unlink(missing_ok=True)
