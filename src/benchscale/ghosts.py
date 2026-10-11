"""Stand-in solids for reference objects, drawn at their real size.

A ghost is what the design is built around: the tip rack in the dock, the
tubes in the rack. They are shown in the viewer and used in the fit checks,
so a pocket that is too small is a collision, not an opinion.
"""

from __future__ import annotations

import trimesh

from . import geometry as g
from .references import Reference


def ghost(ref: Reference, wells: bool = True) -> trimesh.Trimesh:
    """The reference's envelope, origin at its bottom-front-left corner (cylinders: bottom centre)."""
    if ref.shape == "cylinder":
        body = g.cylinder(ref.d, 0.0, ref.h)
        if ref.features.get("conical_bottom"):
            tip = min(ref.h * 0.18, ref.d * 0.9)
            cone = trimesh.creation.cone(radius=ref.d / 2, height=tip, sections=64)
            cone.apply_transform(trimesh.transformations.rotation_matrix(3.14159265, (1, 0, 0)))
            cone.apply_translation((0, 0, tip))
            body = g.union([g.cylinder(ref.d, tip, ref.h), cone])
        return body
    body = g.extrude(g.rect(0, 0, ref.x, ref.y), 0.0, ref.z)
    if not (wells and ref.wells):
        return body
    # Mark the wells as shallow dimples on the top face, so the ghost reads as
    # the real object (and a tip rack shows where the tips are) without the cost
    # of modelling every well to its full depth.
    marks = []
    for w in ref.wells[:384]:
        if w.get("shape") == "circular" and w.get("diameter"):
            marks.append(g.cylinder(w["diameter"], ref.z - 1.0, ref.z + 0.5, w["x"], w["y"], sections=24))
        elif w.get("x_size") and w.get("y_size"):
            hx, hy = w["x_size"] / 2, w["y_size"] / 2
            marks.append(g.extrude(g.rect(w["x"] - hx, w["y"] - hy, w["x"] + hx, w["y"] + hy), ref.z - 1.0, ref.z + 0.5))
    return g.difference(body, marks)
