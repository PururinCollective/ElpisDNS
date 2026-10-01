#!/usr/bin/env python3
"""
Generates the two pictures on the site that are not written by hand:

    img/sea-map.svg     South East Asia, one path per country. The network
                        page pulls it in with <use href="img/sea-map.svg#land">
                        and colours it from the stylesheet, so one file
                        serves both themes. Markers and traffic are drawn on
                        top of it by js/app-map.js.

    img/hero-mesh.svg   The mesh of links behind the front page banner, with
                        light running along them. Animated with CSS inside
                        the SVG, so it works as a plain background image.

Run it only when you want to change either picture:

    python tools/make-graphics.py

Coastlines come from world-atlas (Natural Earth 1:50m, public domain), which
is downloaded from jsDelivr on every run. Offline? Pass a copy you already
have with --topojson countries-50m.json.

The map projection is spherical Mercator. js/app-map.js projects the AS
sites and cities with the same numbers, which it reads from the data-proj
attribute on the map in network.html. Change MAP_* below and that attribute
together, or the markers drift off their cities.
"""

import argparse
import json
import math
import random
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TOPOJSON_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json"

# ------------------------------------------------------------------ the map

MAP_LON0, MAP_LON1 = 88.0, 140.0      # left and right edge
MAP_LAT_TOP, MAP_LAT_BOTTOM = 23.0, -11.5
MAP_W = 1040                          # 20 px per degree of longitude

# Clip a little outside the frame so the cut edges are never on screen.
CLIP_MARGIN = 2.0

# Anything smaller than this, in square pixels, is a rock and not an island.
MIN_RING_AREA = 1.2

# Douglas-Peucker tolerance in pixels. Half a pixel is below what anyone
# can see at the size the map is shown.
SIMPLIFY = 0.45


def merc(lat):
    """Latitude to Mercator y, in degree-equivalent units."""
    phi = math.radians(max(-85.0, min(85.0, lat)))
    return math.degrees(math.log(math.tan(math.pi / 4 + phi / 2)))


MAP_K = MAP_W / (MAP_LON1 - MAP_LON0)
MAP_Y0 = merc(MAP_LAT_TOP)
MAP_H = round((MAP_Y0 - merc(MAP_LAT_BOTTOM)) * MAP_K)


def project(lon, lat):
    return ((lon - MAP_LON0) * MAP_K, (MAP_Y0 - merc(lat)) * MAP_K)


def decode_arcs(topo):
    """TopoJSON arcs are delta encoded and quantised. Undo both."""
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


def ring_from(indexes, arcs):
    """Stitch a ring from arc references. A negative index runs backwards."""
    ring = []

    for index in indexes:
        points = arcs[index] if index >= 0 else arcs[~index][::-1]

        # Consecutive arcs share their joining point.
        ring.extend(points if not ring else points[1:])

    return ring


def clip_ring(ring, x0, y0, x1, y1):
    """Sutherland-Hodgman against an axis aligned box."""

    def clip(points, inside, cross):
        out = []

        for i, current in enumerate(points):
            previous = points[i - 1]

            if inside(current):
                if not inside(previous):
                    out.append(cross(previous, current))
                out.append(current)
            elif inside(previous):
                out.append(cross(previous, current))

        return out

    def at_x(x):
        def cross(a, b):
            t = (x - a[0]) / (b[0] - a[0])
            return (x, a[1] + t * (b[1] - a[1]))
        return cross

    def at_y(y):
        def cross(a, b):
            t = (y - a[1]) / (b[1] - a[1])
            return (a[0] + t * (b[0] - a[0]), y)
        return cross

    points = ring

    for inside, cross in (
        (lambda p: p[0] >= x0, at_x(x0)),
        (lambda p: p[0] <= x1, at_x(x1)),
        (lambda p: p[1] >= y0, at_y(y0)),
        (lambda p: p[1] <= y1, at_y(y1)),
    ):
        if not points:
            break
        points = clip(points, inside, cross)

    return points


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
        length = math.hypot(dx, dy) or 1e-9

        worst, index = 0.0, None

        for i in range(first + 1, last):
            px, py = points[i]
            distance = abs(dy * px - dx * py + bx * ay - by * ax) / length

            if distance > worst:
                worst, index = distance, i

        if index is not None and worst > tolerance:
            keep[index] = True
            stack.append((first, index))
            stack.append((index, last))

    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, tolerance):
    """
    A closed ring starts and ends on the same point, which gives
    Douglas-Peucker a baseline of zero length and nothing survives. Split
    it at the point farthest from the start and simplify the two halves.
    """
    if len(ring) < 4:
        return ring

    ax, ay = ring[0]
    far = max(range(len(ring)), key=lambda i: math.hypot(ring[i][0] - ax, ring[i][1] - ay))

    return (simplify(ring[:far + 1], tolerance)[:-1] +
            simplify(ring[far:] + [ring[0]], tolerance)[:-1])


def area(points):
    return abs(sum(
        points[i - 1][0] * p[1] - p[0] * points[i - 1][1]
        for i, p in enumerate(points)
    )) / 2


def fmt(value):
    text = f"{value:.1f}"
    return "0" if text in ("0.0", "-0.0") else text.rstrip("0").rstrip(".")


def path_data(rings):
    """Relative commands: about a third smaller than absolute ones."""
    parts = []

    for ring in rings:
        x, y = ring[0]
        out = [f"M{fmt(x)} {fmt(y)}"]
        cx, cy = round(x, 1), round(y, 1)

        steps = []

        for px, py in ring[1:]:
            px, py = round(px, 1), round(py, 1)
            dx, dy = px - cx, py - cy

            if dx or dy:
                steps.append(f"{fmt(dx)} {fmt(dy)}".replace(" -", "-"))
                cx, cy = px, py

        if len(steps) < 2:
            continue

        out.append("l" + " ".join(steps) + "z")
        parts.append("".join(out))

    return "".join(parts)


def load_topology(source):
    if source:
        return json.loads(Path(source).read_text(encoding="utf-8"))

    print(f"Downloading {TOPOJSON_URL}")

    with urllib.request.urlopen(TOPOJSON_URL, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def make_map(topo):
    arcs = decode_arcs(topo)

    box = (MAP_LON0 - CLIP_MARGIN, MAP_LAT_BOTTOM - CLIP_MARGIN,
           MAP_LON1 + CLIP_MARGIN, MAP_LAT_TOP + CLIP_MARGIN)

    countries = []

    for geometry in topo["objects"]["countries"]["geometries"]:
        kind = geometry.get("type")

        if kind == "Polygon":
            polygons = [geometry["arcs"]]
        elif kind == "MultiPolygon":
            polygons = geometry["arcs"]
        else:
            continue

        rings = []

        for polygon in polygons:
            for indexes in polygon:
                ring = clip_ring(ring_from(indexes, arcs), *box)

                if len(ring) < 3:
                    continue

                ring = simplify_ring([project(lon, lat) for lon, lat in ring], SIMPLIFY)

                if len(ring) >= 3 and area(ring) >= MIN_RING_AREA:
                    rings.append(ring)

        if rings:
            name = geometry.get("properties", {}).get("name", "")
            countries.append((name, path_data(rings)))

    countries.sort()

    body = "\n".join(
        f'\t\t<path data-name="{name}" d="{d}"/>' for name, d in countries if d
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MAP_W} {MAP_H}">
\t<!--
\t\tSouth East Asia, spherical Mercator, {MAP_LON0:g}E to {MAP_LON1:g}E and
\t\t{MAP_LAT_TOP:g}N to {-MAP_LAT_BOTTOM:g}S. Natural Earth 1:50m via world-atlas.
\t\tGenerated by tools/make-graphics.py - do not edit by hand.

\t\tNo colours on purpose: <use href="img/sea-map.svg#land"> inherits
\t\tfill and stroke from the page, so the stylesheet themes it.
\t-->
\t<g id="land">
{body}
\t</g>
</svg>
"""


# ----------------------------------------------------------- the hero mesh

MESH_W, MESH_H = 1440, 720
MESH_COLS, MESH_ROWS = 9, 5
MESH_SEED = 20260930
MESH_STREAKS = 9


def make_mesh():
    rng = random.Random(MESH_SEED)

    cell_w = MESH_W / (MESH_COLS - 1)
    cell_h = MESH_H / (MESH_ROWS - 1)

    # A jittered grid that spills past the edges, so no line visibly ends.
    nodes = {}

    for row in range(-1, MESH_ROWS + 1):
        for col in range(-1, MESH_COLS + 1):
            nodes[(col, row)] = (
                round(col * cell_w + rng.uniform(-.34, .34) * cell_w),
                round(row * cell_h + rng.uniform(-.34, .34) * cell_h),
            )

    edges = set()

    for (col, row) in nodes:
        for dc, dr in ((1, 0), (0, 1), (1, 1), (1, -1)):
            other = (col + dc, row + dr)

            if other not in nodes:
                continue

            # Every straight link, and about a third of the diagonals.
            if dc and dr and rng.random() > .34:
                continue

            edges.add(((col, row), other))

    neighbours = {key: [] for key in nodes}

    for a, b in edges:
        neighbours[a].append(b)
        neighbours[b].append(a)

    def on_screen(key):
        x, y = nodes[key]
        return -60 <= x <= MESH_W + 60 and -60 <= y <= MESH_H + 60

    # Streaks are random walks, biased to keep moving the same way.
    streaks = []

    while len(streaks) < MESH_STREAKS:
        start = rng.choice([k for k in nodes if k[0] == -1 or k[1] == -1])
        walk = [start]
        heading = (1, 1)

        for _ in range(9):
            options = [n for n in neighbours[walk[-1]] if n not in walk]

            if not options:
                break

            options.sort(key=lambda n: -((n[0] - walk[-1][0]) * heading[0] +
                                         (n[1] - walk[-1][1]) * heading[1]) +
                         rng.uniform(0, 1.4))
            walk.append(options[0])

        if len(walk) >= 6 and sum(on_screen(k) for k in walk) >= 4:
            streaks.append(walk)

    far, near = [], []

    for a, b in sorted(edges):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        line = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
        (near if rng.random() < .45 else far).append(line)

    dots = []

    for key, (x, y) in sorted(nodes.items()):
        if not on_screen(key):
            continue

        big = rng.random() < .3
        cls = "n-hot" if big else "n"
        dots.append(f'<circle class="{cls}" cx="{x}" cy="{y}" r="{5 if big else 2.6}"/>')

    paths, uses = [], []

    for i, walk in enumerate(streaks):
        d = "M" + " L".join(f"{nodes[k][0]} {nodes[k][1]}" for k in walk)
        paths.append(f'<path id="s{i}" pathLength="1000" d="{d}"/>')

        duration = round(rng.uniform(6.5, 11), 1)
        delay = round(-rng.uniform(0, duration), 1)
        tone = " alt" if i % 3 == 1 else ""
        style = f'style="animation-duration:{duration}s;animation-delay:{delay}s"'

        uses.append(f'<use class="tail{tone}" href="#s{i}" {style}/>')
        uses.append(f'<use class="core{tone}" href="#s{i}" {style}/>')

    newline = "\n\t\t"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MESH_W} {MESH_H}" preserveAspectRatio="xMidYMid slice">
\t<!--
\t\tThe mesh behind the front page banner. Generated by
\t\ttools/make-graphics.py - change MESH_* there, not this file.
\t\tFixed colours: it only ever sits on the night-violet hero.
\t-->
\t<style>
\t\t.far line{{stroke:#b9a5ff;stroke-opacity:.10;stroke-width:1}}
\t\t.near line{{stroke:#c9b6ff;stroke-opacity:.22;stroke-width:1.2}}
\t\t.n{{fill:#cbb8ff;fill-opacity:.45}}
\t\t.n-hot{{fill:#ab71ff;fill-opacity:.55}}
\t\tuse{{fill:none;stroke-linecap:round;stroke-linejoin:round;animation:run 8s linear infinite}}
\t\t.tail{{stroke:#9059ff;stroke-opacity:.55;stroke-width:3;stroke-dasharray:80 920}}
\t\t.core{{stroke:#f4eaff;stroke-width:2;stroke-dasharray:10 990}}
\t\t.tail.alt{{stroke:#ff7139}}
\t\t.core.alt{{stroke:#ffe1c4}}
\t\t@keyframes run{{from{{stroke-dashoffset:1000}}to{{stroke-dashoffset:0}}}}
\t\t@media (prefers-reduced-motion:reduce){{use{{display:none}}}}
\t</style>
\t<defs>
\t\t{newline.join(paths)}
\t</defs>
\t<g class="far">
\t\t{newline.join(far)}
\t</g>
\t<g class="near">
\t\t{newline.join(near)}
\t</g>
\t<g>
\t\t{newline.join(dots)}
\t</g>
\t<g>
\t\t{newline.join(uses)}
\t</g>
</svg>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--topojson",
                        help="local countries-50m.json instead of downloading it")
    args = parser.parse_args()

    sea = ROOT / "img" / "sea-map.svg"
    sea.write_text(make_map(load_topology(args.topojson)), encoding="utf-8", newline="\n")
    print(f"Wrote {sea.relative_to(ROOT)} ({sea.stat().st_size // 1024} KB, "
          f'viewBox 0 0 {MAP_W} {MAP_H}, data-proj="{MAP_LON0:g} {MAP_LON1:g} {MAP_LAT_TOP:g}")')

    mesh = ROOT / "img" / "hero-mesh.svg"
    mesh.write_text(make_mesh(), encoding="utf-8", newline="\n")
    print(f"Wrote {mesh.relative_to(ROOT)} ({mesh.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
