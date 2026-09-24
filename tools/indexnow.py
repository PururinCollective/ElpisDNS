#!/usr/bin/env python3
"""
Tells search engines a page changed, instead of waiting for them to notice.

    python tools/indexnow.py              # every URL in sitemap.xml
    python tools/indexnow.py --dry-run    # show what would be sent
    python tools/indexnow.py https://elpis.violetnetworks.xyz/resolver.html

IndexNow is one ping shared by Bing (and so Yahoo and DuckDuckGo, which
draw on Bing's index), Yandex, Naver, Seznam and Yep: tell one, and it
passes the URLs to the rest. Google does not take part; it reads
sitemap.xml, which robots.txt already points at.

Run it after a deploy, not before. The engine fetches the key file from the
live site to check the ping came from whoever owns it, so the key file has
to be published first:

    https://elpis.violetnetworks.xyz/eddcb0f5a2ff7f039dd4e5454e06692a.txt

The key is not a secret - it is public by design. A new one is just a new
32-character hex file at the site root, and KEY below changed to match.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HOST = "elpis.violetnetworks.xyz"
KEY = "eddcb0f5a2ff7f039dd4e5454e06692a"
ENDPOINT = "https://api.indexnow.org/indexnow"

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def sitemap_urls():
    tree = ET.parse(ROOT / "sitemap.xml")
    return [loc.text.strip() for loc in tree.getroot().findall("sm:url/sm:loc", SITEMAP_NS)]


def main():
    parser = argparse.ArgumentParser(description="Ping IndexNow with changed URLs.")
    parser.add_argument("urls", nargs="*", help="URLs to submit (default: all of sitemap.xml)")
    parser.add_argument("--dry-run", action="store_true", help="print the request, send nothing")
    args = parser.parse_args()

    key_file = ROOT / f"{KEY}.txt"
    if not key_file.is_file() or key_file.read_text().strip() != KEY:
        sys.exit(f"{key_file.name} is missing or does not contain the key.")

    urls = args.urls or sitemap_urls()
    foreign = [u for u in urls if not u.startswith(f"https://{HOST}/")]
    if foreign:
        sys.exit("Not on this site: " + ", ".join(foreign))

    body = {
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls,
    }

    if args.dry_run:
        print(f"POST {ENDPOINT}")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return 0

    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
    except urllib.error.HTTPError as err:
        status = err.code
    except urllib.error.URLError as err:
        sys.exit(f"Could not reach {ENDPOINT}: {err.reason}")

    # 200 accepted, 202 accepted but the key is still being checked.
    meaning = {
        200: "accepted",
        202: "accepted, key still being verified",
        400: "bad request",
        403: "key not valid - is the key file live on the site?",
        422: "URLs do not belong to the host, or the key does not match",
        429: "too many requests - try again later",
    }.get(status, "unexpected")

    print(f"{status} {meaning}: {len(urls)} URL{'' if len(urls) == 1 else 's'}")

    return 0 if status in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main())
