"""Style presets — font family, font size, color scheme, with CJK/Latin separation."""
from __future__ import annotations

import re

# ---------- Font families (latin + cjk per role) ----------
FONTS: dict[str, dict[str, str]] = {
    "editorial": {
        "label": "编辑感 · Cormorant + 宋体",
        "display_latin": '"Cormorant Garamond", "Cormorant", Georgia, serif',
        "display_cjk":   '"Source Han Serif SC", "Noto Serif CJK SC", "Songti SC"',
        "body_latin":    '"Cormorant Garamond", Georgia, serif',
        "body_cjk":      '"Source Han Serif SC", "Noto Serif CJK SC", "Songti SC"',
        "mono_latin":    '"JetBrains Mono", Menlo, Consolas, monospace',
        "mono_cjk":      '"Source Han Serif SC", "Songti SC"',
    },
    "modern": {
        "label": "现代 · Inter + 苹方",
        "display_latin": '"Inter", "Helvetica Neue", sans-serif',
        "display_cjk":   '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"',
        "body_latin":    '"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
        "body_cjk":      '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"',
        "mono_latin":    '"JetBrains Mono", "SF Mono", Menlo, Consolas, monospace',
        "mono_cjk":      '"PingFang SC", "Hiragino Sans GB"',
    },
    "academic": {
        "label": "学术 · Times + 宋体",
        "display_latin": '"Times New Roman", serif',
        "display_cjk":   '"Songti SC", "SimSun", "Source Han Serif SC"',
        "body_latin":    '"Times New Roman", serif',
        "body_cjk":      '"Songti SC", "SimSun", "Source Han Serif SC"',
        "mono_latin":    '"Courier New", Menlo, monospace',
        "mono_cjk":      '"Songti SC", "SimSun"',
    },
    "minimal": {
        "label": "极简 · Helvetica + 苹方",
        "display_latin": '"Helvetica Neue", Helvetica, sans-serif',
        "display_cjk":   '"PingFang SC", "Hiragino Sans GB"',
        "body_latin":    '"Helvetica Neue", Helvetica, sans-serif',
        "body_cjk":      '"PingFang SC", "Hiragino Sans GB"',
        "mono_latin":    '"Menlo", "SF Mono", monospace',
        "mono_cjk":      '"PingFang SC", "Hiragino Sans GB"',
    },
}

# ---------- Font sizes (pdf/html base size in pt) ----------
SIZES: dict[str, dict[str, object]] = {
    "compact": {"label": "紧凑 · 10.5pt", "body_pt": 10.5},
    "normal":  {"label": "标准 · 11pt",   "body_pt": 11.0},
    "large":   {"label": "较大 · 12pt",   "body_pt": 12.0},
    "xlarge":  {"label": "很大 · 13pt",   "body_pt": 13.0},
}

# ---------- Color schemes ----------
COLORS: dict[str, dict[str, str]] = {
    "plum": {
        "label": "梅子 × 鼠尾草",
        "heading": "6B5876", "accent": "B8A4C9", "accent_dark": "4E3F5A",
        "rule": "95A89C", "muted": "4E3F5A", "code_bg": "F7F2E9",
    },
    "ink": {
        "label": "墨色 · 极简黑白",
        "heading": "1A1A1A", "accent": "333333", "accent_dark": "000000",
        "rule": "CCCCCC", "muted": "555555", "code_bg": "F4F4F4",
    },
    "sage": {
        "label": "鼠尾草 × 米色",
        "heading": "3D5A4A", "accent": "95A89C", "accent_dark": "2E4438",
        "rule": "B8C6BB", "muted": "4E6155", "code_bg": "F1EFE4",
    },
    "ocean": {
        "label": "靛蓝 × 砂金",
        "heading": "1F3A5F", "accent": "4A6A8C", "accent_dark": "122645",
        "rule": "C8B57A", "muted": "3C4F6B", "code_bg": "F3F1EA",
    },
    "terracotta": {
        "label": "陶土 × 橄榄",
        "heading": "A34A2E", "accent": "C47A5E", "accent_dark": "6E2E1A",
        "rule": "8E9A5F", "muted": "6A4A3A", "code_bg": "F6EEE3",
    },
}

# ---------- Languages ----------
LANGS = [
    {"id": "auto", "label": "自动"},
    {"id": "zh",   "label": "中文为主"},
    {"id": "en",   "label": "英文为主"},
]

DEFAULTS = {"font": "editorial", "size": "normal", "color": "plum", "lang": "auto"}


def get_font(i: str) -> dict[str, str]:
    return FONTS.get(i, FONTS[DEFAULTS["font"]])


def get_size(i: str) -> dict[str, object]:
    return SIZES.get(i, SIZES[DEFAULTS["size"]])


def get_color(i: str) -> dict[str, str]:
    return COLORS.get(i, COLORS[DEFAULTS["color"]])


# ---------- Language detection ----------
_CJK_RE = re.compile(
    r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3000-\u303F\uFF00-\uFFEF]"
)
_SPACE_RE = re.compile(r"\s+")


def detect_lang(md_text: str) -> str:
    """Return 'zh' if CJK characters are >= 5% of non-whitespace chars, else 'en'."""
    stripped = _SPACE_RE.sub("", md_text or "")
    if not stripped:
        return "en"
    cjk = len(_CJK_RE.findall(stripped))
    return "zh" if cjk / len(stripped) >= 0.05 else "en"


def resolve_lang(pref: str, md_text: str) -> str:
    """pref is 'auto' | 'zh' | 'en'. Auto uses detect_lang."""
    if pref == "zh":
        return "zh"
    if pref == "en":
        return "en"
    return detect_lang(md_text)


# ---------- Primary font selectors ----------
def primary_stack(font_id: str, role: str, primary: str) -> str:
    """Compose a CSS font-family value for the given role, ordered by primary language."""
    f = get_font(font_id)
    latin = f.get(f"{role}_latin", "")
    cjk = f.get(f"{role}_cjk", "")
    if primary == "zh":
        return f"{cjk}, {latin}" if cjk and latin else (cjk or latin)
    return f"{latin}, {cjk}" if cjk and latin else (latin or cjk)


def _first_family(stack: str) -> str:
    """Extract the first named family from a CSS font stack."""
    m = re.search(r'"([^"]+)"', stack)
    if m:
        return m.group(1)
    return stack.split(",")[0].strip().strip('"').strip("'")


def primary_name(font_id: str, role: str, primary: str) -> str:
    """Return the primary single font name for DOCX/XLSX (respects primary language)."""
    return _first_family(primary_stack(font_id, role, primary))


def latin_name(font_id: str, role: str) -> str:
    return _first_family(get_font(font_id).get(f"{role}_latin", ""))


def cjk_name(font_id: str, role: str) -> str:
    return _first_family(get_font(font_id).get(f"{role}_cjk", ""))


# ---------- CSS override ----------
def css_override(font_id: str, size_id: str, color_id: str, primary: str) -> str:
    """CSS appended after base stylesheet to override fonts, sizes, colors."""
    s = get_size(size_id)
    c = get_color(color_id)
    base = float(s["body_pt"])  # type: ignore[arg-type]
    body_stack = primary_stack(font_id, "body", primary)
    display_stack = primary_stack(font_id, "display", primary)
    mono_stack = primary_stack(font_id, "mono", primary)
    return f"""
/* user preset: font={font_id} size={size_id} color={color_id} lang={primary} */
html, body {{ font-size: {base}pt !important; }}
html, body, p, li, blockquote, td, th {{ font-family: {body_stack} !important; }}
h1, h2, h3, h4, h5, h6 {{ font-family: {display_stack} !important; }}
code, pre, pre code, kbd, samp {{ font-family: {mono_stack} !important; }}

h1 {{ font-size: {base * 2.3:.1f}pt !important; color: #{c['heading']} !important; border-bottom-color: #{c['accent']} !important; }}
h2 {{ font-size: {base * 1.55:.1f}pt !important; color: #{c['accent_dark']} !important; }}
h3 {{ font-size: {base * 1.22:.1f}pt !important; color: #{c['heading']} !important; }}
h4 {{ font-size: {base * 1.08:.1f}pt !important; color: #{c['accent_dark']} !important; }}

a {{ color: #{c['heading']} !important; text-decoration-color: #{c['accent']} !important; }}
blockquote {{ border-left-color: #{c['rule']} !important; color: #{c['muted']} !important; }}
hr {{ background-color: #{c['rule']} !important; }}

code {{ background: #{c['code_bg']} !important; color: #{c['accent_dark']} !important; }}
pre {{ background: #{c['code_bg']} !important; border-left-color: #{c['accent']} !important; }}
pre code {{ background: transparent !important; }}

th {{ background: #{c['heading']} !important; color: white !important; }}
tr:nth-child(even) td {{ background: #{c['code_bg']} !important; }}
td {{ border-bottom-color: #{c['rule']} !important; }}

.footnotes {{ border-top-color: #{c['accent']} !important; color: #{c['muted']} !important; }}
"""
