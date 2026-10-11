"""Small, dependable solid-modelling helpers (trimesh + manifold).

Two lessons from earlier work are built in: booleans go through manifold, and
2D outlines are cleaned before they are extruded (unions leave duplicate and
collinear points that make leaky solids).
"""

from __future__ import annotations

import math

import numpy as np
import trimesh
from shapely.geometry import LineString, Point, Polygon, box as rect


def clean(poly):
    return poly.buffer(0).simplify(0.002, preserve_topology=True)


def extrude(poly, z0: float, z1: float) -> trimesh.Trimesh:
    """A 2D outline in the XY plane, extruded from z0 to z1."""
    pieces = []
    poly = clean(poly)
    for p in getattr(poly, "geoms", [poly]):
        m = trimesh.creation.extrude_polygon(p, height=z1 - z0)
        m.apply_translation((0, 0, z0))
        pieces.append(m)
    return trimesh.util.concatenate(pieces) if len(pieces) > 1 else pieces[0]


def extrude_yz(poly, x0: float, x1: float) -> trimesh.Trimesh:
    """An outline drawn in the (y, z) plane, extruded along x."""
    m = trimesh.creation.extrude_polygon(clean(poly), height=x1 - x0)          # local (y, z, x)
    m.apply_transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    m.apply_translation((x0, 0, 0))
    return m


def extrude_xz(poly, y0: float, y1: float) -> trimesh.Trimesh:
    """An outline drawn in the (x, z) plane, extruded along y."""
    m = trimesh.creation.extrude_polygon(clean(poly), height=y1 - y0)          # local (x, z, y)
    m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    m.apply_translation((0, y0, 0))
    return m


def rounded_rect(x0: float, y0: float, x1: float, y1: float, r: float):
    r = max(0.0, min(r, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01))
    base = rect(x0, y0, x1, y1)
    return base.buffer(-r, join_style="round").buffer(r, join_style="round", quad_segs=16) if r > 0 else base


def stadium(cx: float, cz: float, length: float, height: float):
    """A slot outline (rounded ends) centred on (cx, cz)."""
    rad = min(length, height) / 2
    if length >= height:
        return LineString([(cx - length / 2 + rad, cz), (cx + length / 2 - rad, cz)]).buffer(rad, 32)
    return LineString([(cx, cz - height / 2 + rad), (cx, cz + height / 2 - rad)]).buffer(rad, 32)


def cylinder(d: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0, sections: int = 64) -> trimesh.Trimesh:
    return extrude(Point(x, y).buffer(d / 2, quad_segs=sections // 4), z0, z1)


def bevelled_slab(outline, z0: float, z1: float, top_bevel: float = 0.0, step: float = 0.1) -> trimesh.Trimesh:
    """An extruded outline whose top edge is bevelled at 45 degrees, in thin slices."""
    if top_bevel <= 0:
        return extrude(outline, z0, z1)
    parts = [extrude(outline, z0, z1 - top_bevel + 0.005)]
    n = max(1, int(round(top_bevel / step)))
    for k in range(n):
        inset = (k + 1) * top_bevel / n
        za = z1 - top_bevel + k * top_bevel / n
        parts.append(extrude(outline.buffer(-inset, join_style="round"), za - 0.005, za + top_bevel / n + 0.005))
    return union(parts)


def lead_in(outline, z_top: float, depth: float, step: float = 0.1) -> list[trimesh.Trimesh]:
    """Cutters that open a pocket's mouth by `depth` at 45 degrees - things drop in."""
    cutters = []
    n = max(1, int(round(depth / step)))
    for k in range(n):
        grow = depth - k * depth / n
        za = z_top - (k + 1) * depth / n
        cutters.append(extrude(outline.buffer(grow, join_style="round").difference(outline.buffer(-0.02)),
                               za - 0.005, (z_top + 1.0 if k == 0 else za + depth / n + 0.005)))
    return cutters


def union(meshes) -> trimesh.Trimesh:
    meshes = [m for m in meshes if m is not None and len(m.faces)]
    return meshes[0] if len(meshes) == 1 else trimesh.boolean.union(meshes, engine="manifold")


def difference(base: trimesh.Trimesh, cutters) -> trimesh.Trimesh:
    cutters = [c for c in cutters if c is not None and len(c.faces)]
    if not cutters:
        return base
    return trimesh.boolean.difference([base, *cutters], engine="manifold")


def intersection(a: trimesh.Trimesh, b: trimesh.Trimesh) -> trimesh.Trimesh:
    return trimesh.boolean.intersection([a, b], engine="manifold")


def overlap_mm3(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    hit = intersection(a, b)
    return 0.0 if hit.is_empty else abs(float(hit.volume))


def largest(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    parts = mesh.split(only_watertight=False)
    return max(parts, key=lambda p: abs(p.volume)) if len(parts) > 1 else mesh


def rotate_x(mesh: trimesh.Trimesh, degrees: float, about=(0, 0, 0)) -> trimesh.Trimesh:
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(degrees), (1, 0, 0), about))
    return m


__all__ = ["Polygon", "Point", "rect", "LineString"]
