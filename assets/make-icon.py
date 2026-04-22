"""Generate a minimal plum-themed app icon for Markdown Converter.

Design: cream round-rect background with a soft plum 'M↓' mark
composed of the letter M + a subtle downward arrow through it,
tying to the plum/sage palette of the app.

Outputs: assets/icon.png (1024x1024) — build-app.sh converts to .icns
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 1024
OUT = Path(__file__).parent / "icon.png"

CREAM = (247, 242, 233, 255)
PLUM = (107, 88, 118, 255)
PLUM_DARK = (78, 63, 90, 255)
SAGE = (149, 168, 156, 255)
PLUM_LIGHT = (184, 164, 201, 120)


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def gradient_bg(size: int) -> Image.Image:
    """Subtle diagonal cream→warmer cream gradient."""
    img = Image.new("RGB", (size, size), CREAM[:3])
    top = (252, 247, 239)
    bot = (241, 233, 220)
    for y in range(size):
        t = y / size
        r = int(top[0] * (1 - t) + bot[0] * t)
        g = int(top[1] * (1 - t) + bot[1] * t)
        b = int(top[2] * (1 - t) + bot[2] * t)
        ImageDraw.Draw(img).line([(0, y), (size, y)], fill=(r, g, b))
    return img


def pick_font(size_pt: int) -> ImageFont.FreeTypeFont:
    """Try a few display serifs; fall back to default."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Cormorant Garamond.ttf",
        "/Library/Fonts/Cormorant Garamond.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/NewYork.ttf",
        "/System/Library/Fonts/Times.ttc",
        "/System/Library/Fonts/Georgia.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size_pt)
            except Exception:
                continue
    return ImageFont.load_default()


def main() -> None:
    bg = gradient_bg(SIZE).convert("RGBA")

    # soft inner shadow near edges for depth
    shadow_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow_layer)
    d.ellipse((-SIZE * 0.2, -SIZE * 0.2, SIZE * 1.2, SIZE * 1.2), outline=(78, 63, 90, 20), width=160)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(40))
    bg = Image.alpha_composite(bg, shadow_layer)

    # Draw big italic 'M' in plum, slightly offset up
    font = pick_font(int(SIZE * 0.78))
    letter = "M"
    tmp = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bbox = td.textbbox((0, 0), letter, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (SIZE - w) // 2 - bbox[0]
    y = (SIZE - h) // 2 - bbox[1] - int(SIZE * 0.04)
    td.text((x, y), letter, fill=PLUM_DARK, font=font)
    bg = Image.alpha_composite(bg, tmp)

    # Sage downward arrow below the M — signals "conversion"
    arrow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arrow)
    cx = SIZE // 2
    top_y = int(SIZE * 0.72)
    bot_y = int(SIZE * 0.88)
    # shaft
    ad.line([(cx, top_y), (cx, bot_y)], fill=SAGE, width=int(SIZE * 0.028))
    # head
    head_w = int(SIZE * 0.08)
    head_h = int(SIZE * 0.06)
    ad.polygon(
        [(cx - head_w, bot_y - head_h), (cx + head_w, bot_y - head_h), (cx, bot_y + int(SIZE * 0.015))],
        fill=SAGE,
    )
    bg = Image.alpha_composite(bg, arrow)

    # Apply rounded-rect mask (macOS Big Sur squircle-ish)
    mask = rounded_mask(SIZE, radius=int(SIZE * 0.22))
    final = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    final.paste(bg, (0, 0), mask=mask)

    final.save(OUT, "PNG")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
