"""Draw docs/shake_fill_section.svg: a cut through one row of the shake-fill deck.

It shows the three things the design relies on, at true scale, from the same
geometry the template builds: a tip arriving point first drops in; a tip
arriving collar first cannot; a filled hole stands up as a bump.
Run:  python tools/section_figure.py
"""

from __future__ import annotations

import math
from pathlib import Path

from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union
from trimesh.intersections import mesh_plane

from benchscale.references import Library
from benchscale.templates import registry

S = 7.0                 # px per mm
OUT = Path(__file__).resolve().parent.parent / "docs" / "shake_fill_section.svg"


def tip_outline(L, collar, ch, body, point, x, z, angle_deg=0.0):
    """Tip silhouette with its point at (x, z), tilted angle_deg from vertical (point down)."""
    pts = [(-point / 2, 0), (point / 2, 0), (body / 2, L - ch), (collar / 2, L - ch), (collar / 2, L),
           (-collar / 2, L), (-collar / 2, L - ch), (-body / 2, L - ch)]
    a = math.radians(angle_deg)
    return [(x + u * math.cos(a) + v * math.sin(a), z - u * math.sin(a) + v * math.cos(a)) for u, v in pts]


def main() -> None:
    lib = Library()
    t = registry()["shake_fill_rack"]
    p = t.resolve({"piece": "deck", "rows": 1, "cols": 5}, lib)
    d = t.build(p, lib)
    q = d.params
    L, collar, ch, body, hole = q["tip_length"], q["collar_od"], q["collar_h"], q["body_od"], q["hole"]
    point, floor = 0.8, q["floor"]
    deck = d.part
    yc = float(deck.bounds[:, 1].mean())
    segments = mesh_plane(deck, plane_normal=[0, 1, 0], plane_origin=[0, yc, 0])
    lines = unary_union([LineString([(s0[0], s0[2]), (s1[0], s1[2])]) for s0, s1 in segments])
    polys = list(polygonize(lines))

    x0, x1 = deck.bounds[0][0], deck.bounds[1][0]
    pitch = q["pitch"]
    centres = [x0 + (x1 - x0 - 4 * pitch) / 2 + i * pitch for i in range(5)]
    hang = L - ch - floor
    top = max(v[1] for poly in polys for v in poly.exterior.coords)

    zmin, zmax = -hang - 16, L + floor + 14
    LEFT, RIGHT = 50.0, 66.0
    W, H = (x1 - x0 + LEFT + RIGHT) * S, (zmax - zmin) * S

    def X(x):
        return (x - x0 + LEFT) * S

    def Z(z):
        return (zmax - z) * S

    def path(pts):
        return "M " + " L ".join(f"{X(a):.1f},{Z(b):.1f}" for a, b in pts) + " Z"

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
           'font-family="Helvetica, Arial, sans-serif" font-size="13">',
           f'<rect width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>']
    for poly in polys:
        d_ = path(poly.exterior.coords)
        for ring in poly.interiors:
            d_ += " " + path(ring.coords)
        out.append(f'<path d="{d_}" fill="#d08a3c" stroke="#7a4a17" stroke-width="1" fill-rule="evenodd"/>')

    tip_style = 'fill="#f6d55c" fill-opacity="0.85" stroke="#8a6d00" stroke-width="1"'
    seated_z = floor - (L - ch)
    for i in (0, 1, 3):                                   # filled holes
        out.append(f'<path d="{path(tip_outline(L, collar, ch, body, point, centres[i], seated_z))}" {tip_style}/>')
    # hole 3: a tip arriving point first, tilted
    arriving = tip_outline(L, collar, ch, body, point, centres[2] + 1.2, top + 1.5, angle_deg=-22)
    out.append(f'<path d="{path(arriving)}" {tip_style} stroke-dasharray="4 3"/>')
    # hole 5: a tip upside down - its collar stops on the ledge, it cannot go through
    upright = tip_outline(L, collar, ch, body, point, centres[4], 0.0)
    flipped = [(x, (L - z) + floor) for x, z in upright]
    out.append(f'<path d="{path(flipped)}" fill="#e35d5d" fill-opacity="0.75" stroke="#8a1f1f" stroke-width="1"/>')

    def label(x, z, text, anchor="start", colour="#222"):
        out.append(f'<text x="{X(x):.1f}" y="{Z(z):.1f}" text-anchor="{anchor}" fill="{colour}">{text}</text>')

    proud = next(c.value for c in d.checks if c.name == "filled holes stand above the funnels")
    peaks = floor + q["pocket_depth"] + (pitch / math.sqrt(2) - (collar + 0.6 + q["hole_comp"]) / 2)
    out.append(f'<line x1="{X(x0):.1f}" y1="{Z(peaks):.1f}" x2="{X(x1):.1f}" y2="{Z(peaks):.1f}" '
               'stroke="#7a4a17" stroke-dasharray="5 4" stroke-width="1"/>')
    label(x1 + 2, peaks - 1, "funnel peaks (on the", colour="#7a4a17")
    label(x1 + 2, peaks - 5, "diagonals, off this cut)", colour="#7a4a17")
    label(x0 - 2, floor + ch + 1, "filled: a bump, not a dip", "end", "#5b4a00")
    label(x0 - 2, floor + ch - 3, proud, "end", "#5b4a00")
    tx, tz = max(arriving, key=lambda v: v[1])
    label(tx, tz + 3, "point first: drops in", "middle")
    label(centres[4], L + floor + 9, "collar first: stops on the ledge", "middle", "#8a1f1f")
    label(centres[4], L + floor + 4, f"hole {hole:g} &lt; collar {collar:g} mm; topples when shaken", "middle", "#8a1f1f")
    label(x0 - 2, floor / 2 - 1, "deck", "end", "#7a4a17")
    label(x1 + 3, -hang + 2, f"tips hang {hang:.0f} mm", colour="#555")
    label(x1 + 3, -hang - 2, "below the deck", colour="#555")
    out.append(f'<line x1="{X(x0)}" y1="{Z(-hang - 4)}" x2="{X(x0 + 10)}" y2="{Z(-hang - 4)}" stroke="#2a9d6a" stroke-width="3"/>')
    label(x0 + 12, -hang - 5, "10 mm", colour="#2a9d6a")
    label(x0 - LEFT + 3, zmin + 3, f"Cut through one row of the shake-fill deck at true scale. Tip sizes are the "
          f"ESTIMATED Axygen T-200-Y values.", colour="#555")
    out.append("</svg>")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(out))
    print(OUT)


if __name__ == "__main__":
    main()
