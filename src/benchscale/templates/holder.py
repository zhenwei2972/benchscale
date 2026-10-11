"""A holder block for any single object - box or cylinder - at its real size."""

from __future__ import annotations

from .. import geometry as g
from ..ghosts import ghost
from ..references import Library
from . import Check, Design, Param, Placed, Template


class Holder(Template):
    name = "holder"
    title = "Holder for one object"
    summary = ("A block with a pocket shaped to one reference object (a box such as a plate or slide, or a "
               "cylinder such as a bottle or tube), with a lead-in and an optional finger notch.")
    params = [
        Param("object", "reference", "std:sbs_footprint", "What it holds - a reference id or a measured one."),
        Param("clearance", "float", 0.5, "Gap per side.", "mm", 0.2, 3.0),
        Param("wall", "float", 3.0, "Wall thickness.", "mm", 1.6, 15.0),
        Param("floor", "float", 2.0, "Floor thickness.", "mm", 1.0, 10.0),
        Param("depth", "float", 0.0, "Pocket depth. 0 = flush for objects under 6 mm, else a third of the height (4 to 30 mm).", "mm", 0.0, 120.0),
        Param("finger_notch", "bool", True, "A U-notch in the front wall to lift the object out."),
    ]

    def build(self, p: dict, lib: Library) -> Design:
        ref = lib.get(p["object"])
        c, w, fl = p["clearance"], p["wall"], p["floor"]
        # Thin things (a slide, a coverslip box) sit flush; tall ones sit a third deep.
        depth = p["depth"] or (ref.height if ref.height < 6 else min(30.0, max(4.0, ref.height / 3)))
        fx, fy = ref.footprint
        W, D = fx + 2 * c + 2 * w, fy + 2 * c + 2 * w
        H = fl + depth
        if ref.shape == "cylinder":
            outline = g.Point(W / 2, D / 2).buffer(W / 2, quad_segs=32)
            pocket = g.Point(W / 2, D / 2).buffer(fx / 2 + c, quad_segs=48)
        else:
            outline = g.rounded_rect(0, 0, W, D, 3.0)
            pocket = g.rect(w, w, w + fx + 2 * c, w + fy + 2 * c)
        body = g.bevelled_slab(outline, 0.0, H, top_bevel=0.6)
        cuts = [g.extrude(pocket, fl, H + 1)] + g.lead_in(pocket, H, 0.6)
        if p["finger_notch"] and ref.shape == "box" and depth > 5:
            notch = g.stadium(W / 2, fl + depth * 0.35 + 30, min(30.0, fx * 0.5), 60)
            cuts.append(g.extrude_xz(notch, -1.0, w + c + 0.5))
        part = g.largest(g.difference(body, cuts))
        obj = ghost(ref)
        obj.apply_translation((W / 2, D / 2, fl + 0.01) if ref.shape == "cylinder" else (w + c, w + c, fl + 0.01))
        design = Design(self.name, {**p, "depth": depth}, part,
                        ghosts=[Placed(ref.name, ref.id, obj)], references=[ref])
        design.checks.append(Check("object standing above the holder", None, f"{ref.height - depth:.1f} mm"))
        design.notes.append(f"Pocket {fx + 2 * c:.2f} x {fy + 2 * c:.2f} mm for {ref.size_text()} ({ref.confidence}).")
        return design
