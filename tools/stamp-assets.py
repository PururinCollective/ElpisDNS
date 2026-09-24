#!/usr/bin/env python3
"""
Stamps local asset links with a content hash, so a changed file lands on a
new URL and Cloudflare has no choice but to fetch it again.

    <link href="style-main.css">          ->  style-main.css?hash=1f4ac0d2
    <script src="js/app.js?version=3.9">  ->  js/app.js?hash=9b2e77aa
    fetch("dns.json")                     ->  dns.json?hash=44c1ba03

Run it after changing any CSS, JS, JSON or image and commit the result:

    python tools/stamp-assets.py

Other modes:

    --check      change nothing, exit 1 if any stamp is stale (for CI)
    --dry-run    print what would change, exit 0
    --ext        extensions to stamp (default css,js,json,svg,png,ico)
    --length     hex characters to keep (default 8)

Notes
-----
The hash is the first 8 hex characters of the file's SHA-256: 32 bits, so a
collision between two versions of the same file is not something you will
live to see.

Nothing is rewritten unless the referenced file actually exists on disk, so
a quoted string that merely looks like a path is left alone. Absolute URLs
(the jsDelivr and Google Fonts links) are skipped - we cannot hash what we
do not host.

References chain: index.html points at js/app.js, which points at dns.json;
style-main.css points at the generated hero map. Stamping dns.json changes
app.js, which changes app.js's own hash, which index.html then has to catch
up with. So the tool runs repeatedly until a pass changes nothing.

Cloudflare includes the query string in its cache key by default, which is
what makes this work. If the zone is set to "Ignore Query String" caching,
turn that off or this buys you nothing.
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SCAN = ("*.html", "js/*.js", "*.css")
# png and ico too: browsers and Cloudflare hold on to a favicon longer than
# anything else, so a new one never shows up without a new URL.
DEFAULT_EXT = "css,js,json,svg,png,ico"
DEFAULT_LENGTH = 8
MAX_PASSES = 10

# Anything with a scheme, or protocol relative, belongs to somebody else.
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.\-]*:|//)", re.I)

# A quoted string that looks like "path/to/file.ext" with an optional
# ?query and #fragment. Deliberately loose - the existence check below is
# what decides whether it is really an asset.
REFERENCE = re.compile(
    r"""(?P<quote>["'])"""
    r"""(?P<path>[^"'<>\s?#]+\.(?P<ext>[A-Za-z0-9]+))"""
    r"""(?P<query>\?[^"'#]*)?"""
    r"""(?P<frag>\#[^"']*)?"""
    r"""(?P=quote)"""
)


def digest_of(path, length):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:length]


def restamp(query, digest):
    """Drop any existing hash/version parameter, keep the rest, append ours."""
    kept = []

    if query:
        for part in query.lstrip("?").split("&"):
            if not part:
                continue
            if part.split("=", 1)[0] in ("hash", "version"):
                continue
            kept.append(part)

    kept.append(f"hash={digest}")

    return "?" + "&".join(kept)


def resolve(ref, source):
    """
    Where a reference points, or None if it is not one of ours.

    Tried against the site root first, because every page sits there and
    that is how the browser resolves it, then next to the file itself.
    """
    if EXTERNAL.match(ref) or ref.startswith("/"):
        return None

    for base in (ROOT, source.parent):
        candidate = (base / ref).resolve()

        if candidate.is_file() and ROOT in candidate.parents:
            return candidate

    return None


def stamp_file(source, exts, length, write):
    original = source.read_bytes()
    text = original.decode("utf-8")

    hits = []

    def replace(match):
        ext = match.group("ext").lower()

        if ext not in exts:
            return match.group(0)

        target = resolve(match.group("path"), source)

        if target is None:
            return match.group(0)

        digest = digest_of(target, length)
        query = restamp(match.group("query"), digest)

        rebuilt = (match.group("quote") + match.group("path") + query +
                   (match.group("frag") or "") + match.group("quote"))

        if rebuilt != match.group(0):
            hits.append((match.group("path"), digest))

        return rebuilt

    updated = REFERENCE.sub(replace, text)

    if hits and write:
        # Bytes in, bytes out: this repo mixes LF and CRLF files and it is
        # not this tool's business to unify them.
        source.write_bytes(updated.encode("utf-8"))

    return hits


def collect(patterns):
    found = []

    for pattern in patterns:
        found.extend(sorted(ROOT.glob(pattern)))

    return [p for p in found if p.is_file()]


def main():
    parser = argparse.ArgumentParser(
        description="Stamp local asset links with a content hash.")
    parser.add_argument("--check", action="store_true",
                        help="change nothing, exit 1 if a stamp is stale")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would change, change nothing")
    parser.add_argument("--ext", default=DEFAULT_EXT,
                        help=f"extensions to stamp (default {DEFAULT_EXT})")
    parser.add_argument("--length", type=int, default=DEFAULT_LENGTH,
                        help=f"hex characters to keep (default {DEFAULT_LENGTH})")
    parser.add_argument("--scan", nargs="*", default=list(DEFAULT_SCAN),
                        help=f"globs to scan (default {' '.join(DEFAULT_SCAN)})")
    args = parser.parse_args()

    write = not (args.check or args.dry_run)
    exts = {e.strip().lower().lstrip(".") for e in args.ext.split(",") if e.strip()}

    sources = collect(args.scan)

    if not sources:
        print("Nothing to scan.")
        return 0

    total = 0

    for attempt in range(1, MAX_PASSES + 1):
        changed = 0

        for source in sources:
            hits = stamp_file(source, exts, args.length, write)

            if hits:
                changed += len(hits)
                rel = source.relative_to(ROOT).as_posix()

                for ref, digest in hits:
                    print(f"  {rel:16s} {ref} -> ?hash={digest}")

        total += changed

        # Without writing there is nothing to converge on, and one pass is
        # enough to know whether anything is stale.
        if not changed or not write:
            break

        if attempt == MAX_PASSES:
            print("Gave up: references keep changing. A reference loop?",
                  file=sys.stderr)
            return 2

    scanned = f"{len(sources)} file{'' if len(sources) == 1 else 's'}"

    if args.check:
        if total:
            print(f"\n{total} stale stamp(s) in {scanned}. "
                  f"Run: python tools/stamp-assets.py")
            return 1

        print(f"All stamps current across {scanned}.")
        return 0

    if not total:
        print(f"All stamps current across {scanned}.")
        return 0

    verb = "would update" if args.dry_run else "updated"
    print(f"\n{verb} {total} reference(s) across {scanned}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
