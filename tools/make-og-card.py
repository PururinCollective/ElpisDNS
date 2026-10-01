#!/usr/bin/env python3
"""
Renders the social cards: the picture Discord, Telegram, X, Facebook and
friends show when a page is shared.

    python tools/make-og-card.py              every card in tools/cards/
    python tools/make-og-card.py ml-dsa-44    just that one

Each tools/cards/<name>.html is a 1200 x 630 page. It is opened in headless
Firefox, photographed, and saved as img/og-<name>.jpg, which the page it
belongs to names in og:image and twitter:image.

Needs Firefox and Pillow (pip install pillow). Firefox runs with a throwaway
profile, so it does not touch, or wait for, the one you browse with.

The cards load their fonts from Google Fonts with font-display:block, so a
card with no network renders in the fallback fonts. Look at the JPEG before
you commit it.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "tools" / "cards"
OUT = ROOT / "img"

WIDTH, HEIGHT = 1200, 630

# Platforms recompress whatever they are given; past this, extra quality
# only makes the file bigger for the crawler that fetches it.
JPEG_QUALITY = 88


def firefox():
    for name in ("firefox", "firefox-esr"):
        path = shutil.which(name)
        if path:
            return path

    sys.exit("Firefox not found. Install it, or put it on PATH.")


def render(card, browser):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is needed for the JPEG: pip install pillow")

    target = OUT / f"og-{card.stem}.jpg"

    with tempfile.TemporaryDirectory() as tmp:
        shot = Path(tmp) / "shot.png"
        profile = Path(tmp) / "profile"
        profile.mkdir()

        subprocess.run(
            [browser, "--headless", "--no-remote", "--profile", str(profile),
             f"--window-size={WIDTH},{HEIGHT}",
             "--screenshot", str(shot), card.as_uri()],
            check=True, timeout=120,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not shot.exists():
            sys.exit(f"Firefox did not write a screenshot for {card.name}")

        with Image.open(shot) as image:
            image = image.convert("RGB")

            if image.size != (WIDTH, HEIGHT):
                image = image.crop((0, 0, WIDTH, HEIGHT))

            image.save(target, "JPEG", quality=JPEG_QUALITY,
                       optimize=True, progressive=True)

    print(f"Wrote {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB)")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("names", nargs="*",
                        help="card names, without .html (default: all)")
    args = parser.parse_args()

    if args.names:
        cards = [CARDS / f"{name}.html" for name in args.names]
    else:
        cards = sorted(CARDS.glob("*.html"))

    missing = [c.name for c in cards if not c.is_file()]

    if missing:
        sys.exit(f"No such card: {', '.join(missing)}")

    browser = firefox()

    for card in cards:
        render(card, browser)


if __name__ == "__main__":
    main()
