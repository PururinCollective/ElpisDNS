#!/usr/bin/env python3
"""
Builds the land under the network map: South East Asia and enough of its
neighbours that panning does not fall off the edge of the world.

    python tools/make-sea-map.py

Writes img/sea-map.json. js/app-map.js draws it as inline SVG, so the land
takes its colours from the page's theme tokens rather than from this file.

The source is Natural Earth 1:50m by way of the world-atlas TopoJSON on
jsDelivr. 1:110m would be a third of the size, but it has no Singapore,
and a map of our network without Singapore on it is not much of a map.

Other modes:

    --source FILE   read a local countries-50m.json instead of downloading
    --tolerance PX  simplification in output pixels (default 0.35)

How the numbers fit together
----------------------------
The projection is Web Mercator, scaled so one degree of longitude is SCALE
units wide, with (0, 0) at the north west corner of BBOX. app-map.js
repeats the same three lines of maths to put the resolvers on top, so if
you change BBOX or SCALE here, nothing else needs to change - both read
them from the JSON.

Every ring is clipped to BBOX before it is simplified, which keeps China,
India and Australia from shipping their whole coastlines for the sake of
the corner of the map they appear in.
"""

import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "img" / "sea-map.json"

SOURCE_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json"

# west, south, east, north - in degrees
BBOX = (78.0, -24.0, 152.0, 34.0)

# Output units per degree of longitude
SCALE = 20.0

# ISO 3166-1 numeric codes. These get the brighter fill; everything else
# is the neighbourhood.
SEA = {
    "096": "Brunei",
    "104": "Myanmar",
    "116": "Cambodia",
    "360": "Indonesia",
    "418": "Laos",
    "458": "Malaysia",
    "608": "Philippines",
    "626": "Timor-Leste",
    "702": "Singapore",
    "704": "Vietnam",
    "764": "Thailand",
}


# ---------- projection ----------

def merc(lat):
    """Mercator northing, in degree-equivalent units."""
    rad = math.radians(max(-85.0, min(85.0, lat)))
    return math.degrees(math.log(math.tan(math.pi / 4 + rad / 2)))


def project(lon, lat):
    west, _, _, north = BBOX
    return ((lon - west) * SCALE, (merc(north) - merc(lat)) * SCALE)


def frame():
    west, south, east, north = BBOX
    width = (east - west) * SCALE
    height = (merc(north) - merc(south)) * SCALE
    return width, height


# ---------- topojson ----------

def decode_arcs(topo):
    """Quantised, delta-encoded arcs back into longitude and latitude."""
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]

    arcs = []

    for arc in topo["arcs"]:
        x = y = 0
        points = []

        for dx, dy in arc:
            x += dx
            y += dy
            points.append((x * sx + tx, y * sy + ty))

        arcs.append(points)

    return arcs


def ring_of(indexes, arcs):
    """Stitch arc references into one ring. ~i means arc i, reversed."""
    ring = []

    for index in indexes:
        points = arcs[~index][::-1] if index < 0 else arcs[index]

        # Consecutive arcs share their joining point.
        ring.extend(points[1:] if ring else points)

    return ring


def polygons_of(geometry, arcs):
    kind = geometry.get("type")

    if kind == "Polygon":
        return [[ring_of(r, arcs) for r in geometry["arcs"]]]

    if kind == "MultiPolygon":
        return [[ring_of(r, arcs) for r in poly] for poly in geometry["arcs"]]

    return []


# ---------- geometry ----------

def clip(ring, width, height):
    """Sutherland-Hodgman against the frame, a few units of slack each side."""
    pad = 4.0
    edges = (
        (lambda p: p[0] >= -pad, lambda a, b: cross_x(a, b, -pad)),
        (lambda p: p[0] <= width + pad, lambda a, b: cross_x(a, b, width + pad)),
        (lambda p: p[1] >= -pad, lambda a, b: cross_y(a, b, -pad)),
        (lambda p: p[1] <= height + pad, lambda a, b: cross_y(a, b, height + pad)),
    )

    for inside, cut in edges:
        if not ring:
            break

        output = []
        prev = ring[-1]

        for point in ring:
            if inside(point):
                if not inside(prev):
                    output.append(cut(prev, point))
                output.append(point)
            elif inside(prev):
                output.append(cut(prev, point))

            prev = point

        ring = output

    return ring


def cross_x(a, b, x):
    t = (x - a[0]) / (b[0] - a[0])
    return (x, a[1] + t * (b[1] - a[1]))


def cross_y(a, b, y):
    t = (y - a[1]) / (b[1] - a[1])
    return (a[0] + t * (b[0] - a[0]), y)


def simplify(points, tolerance):
    """Douglas-Peucker, iterative so a long coastline cannot blow the stack."""
    if len(points) < 4:
        return points

    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]

    while stack:
        first, last = stack.pop()
        ax, ay = points[first]
        bx, by = points[last]
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)

        worst, index = 0.0, None

        for i in range(first + 1, last):
            px, py = points[i]

            # A closed ring starts and ends on the same point, so the first
            # split has no line to measure against - measure to the point.
            if length == 0:
                distance = math.hypot(px - ax, py - ay)
            else:
                distance = abs(dy * px - dx * py + bx * ay - by * ax) / length

            if distance > worst:
                worst, index = distance, i

        if index is not None and worst > tolerance:
            keep[index] = True
            stack.append((first, index))
            stack.append((index, last))

    return [p for p, k in zip(points, keep) if k]


def area(ring):
    return abs(sum(
        a[0] * b[1] - b[0] * a[1]
        for a, b in zip(ring, ring[1:] + ring[:1])
    )) / 2


def path_of(rings):
    """Relative SVG path data, one decimal place. Relative moves are short."""
    parts = []

    for ring in rings:
        x0, y0 = round(ring[0][0], 1), round(ring[0][1], 1)
        cmd = [f"M{fmt(x0)} {fmt(y0)}"]
        px, py = x0, y0

        for x, y in ring[1:]:
            x, y = round(x, 1), round(y, 1)
            dx, dy = round(x - px, 1), round(y - py, 1)

            if dx == 0 and dy == 0:
                continue

            cmd.append(f"l{fmt(dx)} {fmt(dy)}")
            px, py = x, y

        cmd.append("z")
        parts.append("".join(cmd))

    return "".join(parts).replace(" -", "-")


def fmt(value):
    text = f"{value:.1f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


# ---------- main ----------

def load(source):
    if source:
        return json.loads(Path(source).read_text(encoding="utf-8"))

    print(f"Downloading {SOURCE_URL}")

    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Build img/sea-map.json.")
    parser.add_argument("--source", help="local countries-50m.json")
    parser.add_argument("--tolerance", type=float, default=0.35,
        help="simplification in output pixels (default 0.35)")
    args = parser.parse_args()

    topo = load(args.source)
    arcs = decode_arcs(topo)
    width, height = frame()

    countries = []

    for geometry in topo["objects"]["countries"]["geometries"]:
        rings = []

        for polygon in polygons_of(geometry, arcs):
            for ring in polygon:
                projected = [project(lon, lat) for lon, lat in ring]
                clipped = clip(projected, width, height)

                if len(clipped) < 3:
                    continue

                simple = simplify(clipped + [clipped[0]], args.tolerance)[:-1]

                # A rock smaller than a pixel squared is not worth a path.
                if len(simple) >= 3 and area(simple) >= 0.6:
                    rings.append(simple)

        if not rings:
            continue

        code = geometry.get("id")

        countries.append({
            "id": code,
            "name": geometry["properties"].get("name", ""),
            "sea": code in SEA,
            "d": path_of(rings),
        })

    # Neighbours first, so SEA borders are drawn on top of them.
    countries.sort(key=lambda c: (c["sea"], c["name"]))

    west, south, east, north = BBOX

    data = {
        "//": "Generated by tools/make-sea-map.py from Natural Earth 1:50m. Do not edit by hand.",
        "bbox": [west, south, east, north],
        "scale": SCALE,
        "width": round(width, 1),
        "height": round(height, 1),
        "countries": countries,
    }

    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8")

    size = OUT.stat().st_size
    sea = sum(1 for c in countries if c["sea"])

    print(f"Wrote {OUT.relative_to(ROOT).as_posix()}: {len(countries)} countries "
        f"({sea} in South East Asia), {size / 1024:.0f} KiB")

    missing = set(SEA) - {c["id"] for c in countries}

    if missing:
        print("Missing: " + ", ".join(SEA[m] for m in sorted(missing)), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
