#!/usr/bin/env python3
"""
Draws the images the site hands to other people's software:

    img/og-*.png         1200x630 share cards, one per page, for Facebook,
                         X, Discord, Telegram, LinkedIn, Slack, WhatsApp...
    img/icon-192.png     the shield mark, for the manifest and search results
    img/icon-512.png     the same, larger; also the Organization logo
    img/icon-maskable-512.png
                         the mark on a solid square with room to spare, for
                         Android launchers that crop icons into circles
    img/apple-touch-icon.png
                         180x180 on a solid square: iOS paints transparency
                         black and rounds the corners itself
    favicon.ico          16 to 256 pixels, each size drawn on its own rather
                         than shrunk from the largest, so the small ones stay
                         sharp. Also what search results show beside a link

    python tools/make-brand-images.py

The front page keeps img/og-image.jpg, the illustration, which is drawn by
hand and not touched here.

Everything is drawn at twice the size and scaled down, which is the cheapest
antialiasing Pillow has. Needs Pillow and Noto Sans (fonts-noto-core on
Debian and Ubuntu) - Noto rather than whatever is lying around, because the
cards spell ΕΛΠΙΣ in Greek.

The colours are the site's dark tokens from style-main.css, and the mark is
img/elpis-mark.svg redrawn from the same path, so a card and the page it
points at look like one thing. To change what a card says, edit CARDS.
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"

W, H = 1200, 630
S = 2

FONT_DIRS = (
    Path("/usr/share/fonts/truetype/noto"),
    Path("/usr/share/fonts/noto"),
    Path("/usr/share/fonts/google-noto"),
)

# style-main.css, dark theme
BAR = "#1b1e24"
TEXT = "#e8ebee"
BODY = "#d5d9de"
SOFT = "#aab1b9"
FAINT = "#8d949d"
ACCENT = "#2f9ee0"

# img/elpis-mark.svg
BLUE_STOPS = ((0.0, "#8fd0f7"), (0.45, "#2f9ee0"), (1.0, "#1f6fa8"))
STEEL_STOPS = ((0.0, "#5c6067"), (1.0, "#2a2d31"))

# One card per page. `badge` is the big figure in the ring and the line
# under it; keep the figure short, it is sized to fit. `cell` picks out one
# cell of the dot lattice - only the ML-DSA card, whose maths it is.
CARDS = (
    {
        "out": "og-ml-dsa-44.png",
        "brand": "Resolver",
        "eyebrow": "POST-QUANTUM DNSSEC",
        "title": "ML-DSA-44",
        "sub": ("The second resolver in the world", "to validate it."),
        "chips": ("FIPS 204", "Algorithm 18", "Open source"),
        "badge": ("2nd", "IN THE WORLD"),
        "cell": True,
    },
    {
        "out": "og-resolver.png",
        "brand": "Resolver",
        "eyebrow": "OUR OWN RECURSIVE RESOLVER",
        "title": "ΕΛΠΙΣ Resolver",
        "sub": ("Straight to the root servers.", "No Google, no Cloudflare."),
        "chips": ("DNSSEC", "ML-DSA-44", "Open source"),
        "badge": ("0.6", "MS FROM CACHE"),
    },
    {
        "out": "og-self-host.png",
        "brand": "Resolver",
        "eyebrow": "RUN YOUR OWN",
        "title": "Self-host ΕΛΠΙΣ",
        "sub": ("From a Raspberry Pi", "to an ISP's server rack."),
        "chips": ("Home lab", "VM", "Bare metal"),
        "badge": ("1.4", "MB, ONE BINARY"),
    },
    {
        "out": "og-mission.png",
        "brand": "DNS",
        "eyebrow": "OUR MISSION",
        "title": "Why ΕΛΠΙΣ exists",
        "sub": ("No logs, no middlemen,", "and only the junk blocked."),
        "chips": ("No logs", "Public blocklists", "Open source"),
        "badge": ("0", "QUERY LOGS"),
    },
    {
        "out": "og-setup.png",
        "brand": "DNS",
        "eyebrow": "SETUP GUIDES",
        "title": "Set up ΕΛΠΙΣ",
        "sub": ("Phones, computers, browsers,", "routers and AdGuard Home."),
        "chips": ("Android", "Windows", "iOS", "MikroTik"),
        "badge": ("8", "SETUP GUIDES"),
    },
)

TITLE_MAX = 118
TITLE_MIN = 64
TITLE_ROOM = 720     # the left column ends before the badge ring


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


def fitted(name, text, largest, smallest, room):
    """The largest size of `name` at which `text` fits in `room` pixels."""
    size = largest
    while size > smallest and font(name, size).getlength(text) > s(room):
        size -= 2
    return font(name, size), size


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
    """img/elpis-mark.svg drawn at size_px square, transparent around it."""
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


def spaced_width(text, fnt, tracking):
    return sum(fnt.getlength(c) + s(tracking) for c in text) - s(tracking)


def card(spec):
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

    # A dot lattice fading in behind the badge.
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

    if spec.get("cell"):
        # One cell picked out: the basis ML-DSA hides a short vector in.
        ox, oy = 470 + 10 * b1[0] + 2 * b2[0], -20 + 2 * b2[1]
        cell = [(ox, oy), (ox + b1[0], oy), (ox + b1[0] + b2[0], oy + b2[1]), (ox + b2[0], oy + b2[1])]
        over = Image.new("RGBA", size, (0, 0, 0, 0))
        od = ImageDraw.Draw(over)
        od.polygon([(s(x), s(y)) for x, y in cell], fill=rgb(ACCENT, 46), outline=rgb(ACCENT, 200), width=s(1.5))
        for x, y in cell:
            od.ellipse((s(x - 3.6), s(y - 3.6), s(x + 3.6), s(y + 3.6)), fill=rgb(ACCENT))
        img.alpha_composite(over)

    # badge
    cx, cy, r = 975, 330, 138
    badge = Image.new("RGBA", size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse((s(cx - r), s(cy - r), s(cx + r), s(cy + r)), fill=rgb(BAR, 235), outline=rgb(ACCENT), width=s(5))
    bd.ellipse((s(cx - r + 14), s(cy - r + 14), s(cx + r - 14), s(cy + r - 14)), outline=rgb(ACCENT, 90), width=s(1.5))
    img.alpha_composite(badge)

    draw = ImageDraw.Draw(img)
    figure, caption = spec["badge"]
    big, _ = fitted("NotoSans-Bold.ttf", figure, 104, 48, 200)
    draw.text((s(cx), s(cy - 8)), figure, font=big, fill=rgb(TEXT), anchor="mm")
    small, tracking = font("NotoSans-Bold.ttf", 17), 3.5
    if spaced_width(caption, small, tracking) > s(206):
        small, tracking = font("NotoSans-Bold.ttf", 15), 2.5
    width = spaced_width(caption, small, tracking)
    spaced(draw, (s(cx) - width / 2, s(cy + 52)), caption, small, rgb(ACCENT), tracking)

    # accent edge along the top, like the cards on the site
    draw.rectangle((0, 0, s(W), s(6)), fill=rgb(ACCENT))

    # brand
    left = 72
    img.alpha_composite(mark(s(52)), (s(left), s(58)))
    x = spaced(draw, (s(left + 68), s(66)), "ΕΛΠΙΣ", font("NotoSans-Bold.ttf", 28), rgb(TEXT), 3)
    draw.text((x + s(10), s(66)), spec["brand"], font=font("NotoSans-Regular.ttf", 28), fill=rgb(SOFT))

    # headline: the title shrinks to fit, and the lines under it follow
    spaced(draw, (s(left), s(196)), spec["eyebrow"], font("NotoSans-Bold.ttf", 22), rgb(ACCENT), 4)
    title_font, title_size = fitted("NotoSans-Bold.ttf", spec["title"], TITLE_MAX, TITLE_MIN, TITLE_ROOM)
    title_y = 222 + (TITLE_MAX - title_size) * 0.35
    draw.text((s(left - 4), s(title_y)), spec["title"], font=title_font, fill=rgb(TEXT))
    sub = font("NotoSans-Regular.ttf", 36)
    sub_y = title_y + title_size * 1.44
    for n, line in enumerate(spec["sub"]):
        draw.text((s(left), s(sub_y + n * 46)), line, font=sub, fill=rgb(BODY))

    # chips
    chip = font("NotoSans-Regular.ttf", 20)
    chips = Image.new("RGBA", size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(chips)
    x = left
    places = []
    for label in spec["chips"]:
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

    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def icon(px, maskable=False):
    """The mark alone. Maskable icons sit on a solid square inside the
    central 80% circle that launchers promise never to crop."""
    if not maskable:
        return mark(px * S).resize((px, px), Image.LANCZOS)

    return on_square(px, 0.68)


def on_square(px, share):
    """The mark centred on a solid square, taking `share` of its width."""
    img = Image.new("RGBA", (px * S, px * S), rgb(BAR))
    inner = int(px * S * share)
    off = (px * S - inner) // 2
    img.alpha_composite(mark(inner), (off, off))
    return img.resize((px, px), Image.LANCZOS)


def report(path, size):
    print(f"  {path.relative_to(ROOT).as_posix():28s} {size}  {path.stat().st_size // 1024} KB")


def save(img, name):
    path = IMG / name
    img.save(path, optimize=True)
    report(path, f"{img.size[0]}x{img.size[1]}")


def save_favicon():
    sizes = (16, 20, 24, 32, 48, 64, 128, 256)
    frames = [icon(n) for n in sizes]
    path = ROOT / "favicon.ico"
    frames[-1].save(path, format="ICO", sizes=[(n, n) for n in sizes], append_images=frames[:-1])
    report(path, ", ".join(str(n) for n in sizes))


def main():
    for spec in CARDS:
        save(card(spec), spec["out"])

    save(icon(192), "icon-192.png")
    save(icon(512), "icon-512.png")
    save(icon(512, maskable=True), "icon-maskable-512.png")
    save(on_square(180, 0.78), "apple-touch-icon.png")
    save_favicon()


if __name__ == "__main__":
    main()
