#!/usr/bin/env python3
"""
Draws img/og-ml-dsa-44.png, the 1200x630 card that Discord, Telegram, X,
Facebook, LinkedIn and friends show when someone shares ml-dsa-44.html.

    python tools/make-og-mldsa.py

Everything is drawn at twice the size and scaled down, which is the cheapest
antialiasing Pillow has. Needs Pillow and Noto Sans (fonts-noto-core on
Debian and Ubuntu) - Noto rather than whatever is lying around, because the
card spells ΕΛΠΙΣ in Greek.

The colours are the site's dark tokens from style-main.css, and the mark is
img/elpis-mark.svg redrawn with the same path, so the card and the page it
points at look like one thing.
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "img" / "og-ml-dsa-44.png"

W, H = 1200, 630
S = 2

FONT_DIRS = (
    Path("/usr/share/fonts/truetype/noto"),
    Path("/usr/share/fonts/noto"),
    Path("/usr/share/fonts/google-noto"),
)

# style-main.css, dark theme
BAR = "#1b1e24"
LINE = "#454b55"
TEXT = "#e8ebee"
SOFT = "#aab1b9"
FAINT = "#8d949d"
ACCENT = "#2f9ee0"

# img/elpis-mark.svg
BLUE_STOPS = ((0.0, "#8fd0f7"), (0.45, "#2f9ee0"), (1.0, "#1f6fa8"))
STEEL_STOPS = ((0.0, "#5c6067"), (1.0, "#2a2d31"))


def s(v):
    return int(round(v * S))


def rgb(hex_colour, alpha=255):
    h = hex_colour.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def font(name, size):
    for folder in FONT_DIRS:
        path = folder / name
        if path.is_file():
            return ImageFont.truetype(str(path), s(size))

    sys.exit(f"{name} not found. Install Noto Sans (fonts-noto-core).")


def gradient(size, p0, p1, stops):
    """A linear gradient from p0 to p1, like SVG's userSpaceOnUse."""
    w, h = size
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    span = dx * dx + dy * dy
    colours = [(at, rgb(c)) for at, c in stops]

    def colour_at(t):
        t = min(max(t, 0.0), 1.0)
        for (a, ca), (b, cb) in zip(colours, colours[1:]):
            if t <= b:
                k = 0.0 if b == a else (t - a) / (b - a)
                return tuple(int(ca[i] + (cb[i] - ca[i]) * k) for i in range(4))
        return colours[-1][1]

    img = Image.new("RGBA", size)
    img.putdata([
        colour_at(((x - p0[0]) * dx + (y - p0[1]) * dy) / span)
        for y in range(h) for x in range(w)
    ])
    return img


def cubic(p0, p1, p2, p3, steps=24):
    out = []
    for i in range(1, steps + 1):
        t = i / steps
        u = 1 - t
        out.append((
            u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
        ))
    return out


def stroke_mask(size, points, width, closed=False):
    """Round joins and round caps, which ImageDraw.line only half does."""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    pts = points + points[:2] if closed else points
    draw.line(pts, fill=255, width=int(width), joint="curve")
    if not closed:
        r = width / 2
        for x, y in (points[0], points[-1]):
            draw.ellipse((x - r, y - r, x + r, y + r), fill=255)
    return mask


def mark(size_px):
    """img/elpis-mark.svg at size_px (already supersampled)."""
    k = size_px / 512
    box = (size_px, size_px)

    def pt(x, y):
        return (x * k, y * k)

    shield = [pt(256, 20), pt(462, 106), pt(462, 272)]
    shield += [pt(*p) for p in cubic((462, 272), (462, 372), (376, 452), (256, 492))]
    shield += [pt(*p) for p in cubic((256, 492), (136, 452), (50, 372), (50, 272))]
    shield += [pt(50, 106)]

    blue = gradient(box, pt(96, 64), pt(416, 464), BLUE_STOPS)
    steel = gradient(box, pt(64, 32), pt(448, 480), STEEL_STOPS)

    img = Image.new("RGBA", box, (0, 0, 0, 0))

    body = Image.new("L", box, 0)
    ImageDraw.Draw(body).polygon(shield, fill=255)
    img.paste(steel, (0, 0), body)

    # dashed routing ring: r=150, 46 on, 34 off
    ring = Image.new("RGBA", box, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    cx, cy, r = 256 * k, 252 * k, 150 * k
    on, off = math.degrees(46 / 150), math.degrees(34 / 150)
    a = -90.0
    while a < 270:
        rd.arc((cx - r, cy - r, cx + r, cy + r), a, min(a + on, 270),
               fill=rgb("#8b9099", 140), width=max(1, int(7 * k)))
        a += on + off
    img.alpha_composite(ring)

    img.paste(blue, (0, 0), stroke_mask(box, shield, 18 * k, closed=True))

    sigma = [pt(332, 162), pt(174, 162), pt(260, 252), pt(174, 342), pt(332, 342)]
    img.paste(blue, (0, 0), stroke_mask(box, sigma, 40 * k))

    return img


def spaced(draw, xy, text, fnt, fill, tracking):
    """Letter-spaced text; returns the x where it ended."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + s(tracking)
    return x


def main():
    size = (s(W), s(H))
    img = Image.new("RGBA", size, rgb(BAR))

    # A soft blue glow, top right, the same one the page heads carry.
    glow = Image.new("L", (W // 4, H // 4), 0)
    ImageDraw.Draw(glow).ellipse((W // 4 * 0.45, -H // 4 * 0.55, W // 4 * 1.25, H // 4 * 0.6), fill=90)
    glow = glow.filter(ImageFilter.GaussianBlur(28)).resize(size, Image.BICUBIC)
    img.paste(Image.new("RGBA", size, rgb(ACCENT)), (0, 0), glow)

    # Translucent fills go on their own layer and are composited: drawn
    # straight onto the image, Pillow replaces the pixel instead of blending.
    dots = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(dots)

    # The lattice ML-DSA is built on, fading in behind the badge.
    b1, b2 = (54, 0), (22, 47)
    for j in range(-2, 16):
        for i in range(-6, 26):
            x = 470 + i * b1[0] + j * b2[0]
            y = -20 + i * b1[1] + j * b2[1]
            if not (0 <= x <= W and 0 <= y <= H):
                continue
            fade = min(max((x - 500) / 420, 0), 1)
            if fade <= 0:
                continue
            r = 2.4
            draw.ellipse((s(x - r), s(y - r), s(x + r), s(y + r)),
                         fill=rgb("#5a616c", int(210 * fade)))
    img.alpha_composite(dots)

    # One cell of it picked out, the basis the scheme hides a short vector in.
    ox, oy = 470 + 10 * b1[0] + 2 * b2[0], -20 + 2 * b2[1]
    cell = [(ox, oy), (ox + b1[0], oy), (ox + b1[0] + b2[0], oy + b2[1]), (ox + b2[0], oy + b2[1])]
    over = Image.new("RGBA", size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    od.polygon([(s(x), s(y)) for x, y in cell], fill=rgb(ACCENT, 46), outline=rgb(ACCENT, 200), width=s(1.5))
    for x, y in cell:
        od.ellipse((s(x - 3.6), s(y - 3.6), s(x + 3.6), s(y + 3.6)), fill=rgb(ACCENT))
    img.alpha_composite(over)

    # "2nd in the world" badge
    cx, cy, r = 975, 330, 138
    badge = Image.new("RGBA", size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse((s(cx - r), s(cy - r), s(cx + r), s(cy + r)), fill=rgb(BAR, 235), outline=rgb(ACCENT), width=s(5))
    bd.ellipse((s(cx - r + 14), s(cy - r + 14), s(cx + r - 14), s(cy + r - 14)), outline=rgb(ACCENT, 90), width=s(1.5))
    img.alpha_composite(badge)

    draw = ImageDraw.Draw(img)
    big = font("NotoSans-Bold.ttf", 104)
    draw.text((s(cx), s(cy - 8)), "2nd", font=big, fill=rgb(TEXT), anchor="mm")
    small = font("NotoSans-Bold.ttf", 17)
    label = "IN THE WORLD"
    width = sum(small.getlength(c) + s(3.5) for c in label) - s(3.5)
    spaced(draw, (s(cx) - width / 2, s(cy + 52)), label, small, rgb(ACCENT), 3.5)

    # accent edge along the top, like the cards on the site
    draw.rectangle((0, 0, s(W), s(6)), fill=rgb(ACCENT))

    # brand
    left = 72
    m = mark(s(52))
    img.alpha_composite(m, (s(left), s(58)))
    brand = font("NotoSans-Bold.ttf", 28)
    x = spaced(draw, (s(left + 68), s(66)), "ΕΛΠΙΣ", brand, rgb(TEXT), 3)
    draw.text((x + s(10), s(66)), "Resolver", font=font("NotoSans-Regular.ttf", 28), fill=rgb(SOFT))

    # headline
    spaced(draw, (s(left), s(196)), "POST-QUANTUM DNSSEC", font("NotoSans-Bold.ttf", 22), rgb(ACCENT), 4)
    draw.text((s(left - 4), s(222)), "ML-DSA-44", font=font("NotoSans-Bold.ttf", 118), fill=rgb(TEXT))
    sub = font("NotoSans-Regular.ttf", 36)
    draw.text((s(left), s(392)), "The second resolver in the world", font=sub, fill=rgb("#d5d9de"))
    draw.text((s(left), s(438)), "to validate it.", font=sub, fill=rgb("#d5d9de"))

    # chips
    chip = font("NotoSans-Regular.ttf", 20)
    chips = Image.new("RGBA", size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(chips)
    x = left
    places = []
    for label in ("FIPS 204", "Algorithm 18", "Open source"):
        tw = chip.getlength(label) / S
        cd.rounded_rectangle((s(x), s(522), s(x + tw + 32), s(560)), radius=s(19),
                             outline=rgb(ACCENT, 170), width=s(1.5), fill=rgb(ACCENT, 30))
        places.append((x, label))
        x += tw + 44
    img.alpha_composite(chips)
    draw = ImageDraw.Draw(img)
    for x, label in places:
        draw.text((s(x + 16), s(541)), label, font=chip, fill=rgb(TEXT), anchor="lm")

    draw.text((s(W - 72), s(541)), "elpis.violetnetworks.xyz",
              font=font("NotoSansMono-Regular.ttf", 19), fill=rgb(FAINT), anchor="rm")

    out = img.convert("RGB").resize((W, H), Image.LANCZOS)
    out.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
