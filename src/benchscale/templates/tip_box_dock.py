"""A tilted, non-slip dock for one pipette tip rack.

The bench problem: in a biosafety cabinet the tip rack sits flat at the back of
the work surface. Every tip pick-up is a reach over the rack, a multichannel
pipette pressed onto a row of tips pushes the rack across the surface, and
fingers have nothing to grip when the rack has to come out. Commercial tilted
or locking tip stands are sold per brand and cost around a hundred dollars.

This dock holds the rack your lab actually uses, tilted toward you, in a pocket
sized from that rack's real footprint, with a low front wall, finger notches on
both sides, a lead-in so the rack drops in, and recesses for silicone feet.
"""

from __future__ import annotations

import math

import numpy as np

from .. import geometry as g
from ..ghosts import ghost
from ..references import Library
from . import Check, Design, Param, Placed, Template

BIG = 200.0


class TipBoxDock(Template):
    name = "tip_box_dock"
    title = "Tilted tip-rack dock"
    summary = ("Holds one pipette tip rack (or any boxed labware) tilted toward the user, in a pocket "
               "sized from its real footprint; low front wall, finger notches, non-slip feet.")
    params = [
        Param("box", "reference", "opentrons:tipone_96_tiprack_200ul",
              "The rack or box the dock holds - a reference id from search_references, or a measured one."),
        Param("tilt_deg", "float", 15.0, "Tilt toward the user.", "deg", 0.0, 30.0),
        Param("clearance", "float", 0.5, "Gap between the box and the pocket wall, per side.", "mm", 0.2, 2.0),
        Param("wall", "float", 3.0, "Pocket wall thickness.", "mm", 1.6, 8.0),
        Param("floor", "float", 2.4, "Thinnest floor, at the front of the pocket.", "mm", 1.2, 10.0),
        Param("pocket_depth", "float", 14.0, "How deep the box sits in the pocket, along the tilted wall.", "mm", 5.0, 40.0),
        Param("front_wall", "float", 6.0, "Height of the lowered front wall, so the pipette can approach.", "mm", 2.0, 40.0),
        Param("finger_notches", "bool", True, "U-notches in both side walls to grip the box."),
        Param("notch_width", "float", 30.0, "Finger notch width.", "mm", 15.0, 60.0),
        Param("feet", "bool", True, "Recesses under the corners for 10 mm stick-on silicone bumpers."),
        Param("max_height", "float", 0.0,
              "Optional limit on the top of the box above the bench (e.g. a cabinet sash). 0 = no limit.", "mm", 0.0, 600.0),
    ]

    def build(self, p: dict, lib: Library) -> Design:
        ref = lib.get(p["box"])
        if ref.shape != "box":
            raise ValueError(f"{ref.name} is a cylinder; the dock holds boxes - try the holder template")
        bx, by = ref.x, ref.y
        c, w, depth = p["clearance"], p["wall"], p["pocket_depth"]
        W, D = bx + 2 * c + 2 * w, by + 2 * c + 2 * w
        x_in0, y_in0, x_in1, y_in1 = w, w, w + bx + 2 * c, w + by + 2 * c
        front_h = min(p["front_wall"], depth)
        t = p["tilt_deg"]

        # --- built with the pocket floor flat at z = 0, then tilted ----------
        outline = g.rounded_rect(0, 0, W, D, 4.0)
        body = g.bevelled_slab(outline, -BIG, depth, top_bevel=0.8)
        pocket = g.rect(x_in0, y_in0, x_in1, y_in1)
        cuts = [g.extrude(pocket, 0.0, depth + 5.0)]
        cuts += g.lead_in(pocket, depth, 0.8)                     # the box drops in
        for cx in (x_in0, x_in1):                                  # corner reliefs: printed
            for cy in (y_in0, y_in1):                              # corners are never sharp
                cuts.append(g.cylinder(3.0, 0.0, depth + 5.0, cx, cy, sections=32))
        # Lower the front wall, ramping the side walls down to it at 45 degrees.
        ramp = g.Polygon([(-1.0, front_h), (w + 0.01, front_h), (w + depth - front_h, depth + 0.01),
                          (w + depth - front_h, depth + 5), (-1.0, depth + 5)])
        cuts.append(g.extrude_yz(ramp, -1.0, W + 1.0))
        if p["finger_notches"]:
            notch_bottom = max(2.0, depth * 0.25)
            height = 2 * (depth - notch_bottom) + 20
            profile = g.stadium(D / 2, notch_bottom + height / 2, min(p["notch_width"], D - 2 * w - 4), height)
            # Through each side wall, with a 1 mm 45-degree flare on the outer
            # face so the notch edge you hold is not square.
            cuts.append(g.extrude_yz(profile, -1.0, w + c + 0.5))          # left wall
            cuts.append(g.extrude_yz(profile, x_in1 - 0.5, W + 1.0))       # right wall
            steps = 8
            for k in range(steps):
                grown = profile.buffer(1.0 - k / steps)
                a, b = k / steps, (k + 1) / steps                          # depth into the wall
                cuts.append(g.extrude_yz(grown, a - (1.0 if k == 0 else 0.005), b + 0.005))
                cuts.append(g.extrude_yz(grown, W - b - 0.005, W - a + (1.0 if k == 0 else 0.005)))
        dock = g.difference(body, cuts)

        box = ghost(ref)
        box.apply_translation((x_in0 + c, y_in0 + c, 0.01))

        # --- tilt toward the user, then sit it on the bench -------------------
        lift = p["floor"] - y_in0 * math.sin(math.radians(t))
        for mesh in (dock, box):
            mesh.apply_transform(_tilt(t, lift))
        dock = g.intersection(dock, g.extrude(g.rect(-50, -50, W + 50, D + 50), 0.0, BIG))
        if p["feet"]:
            x0, y0, _ = dock.bounds[0]
            x1, y1, _ = dock.bounds[1]
            feet = [g.cylinder(10.5, -1.0, 1.2, fx, fy, sections=48)
                    for fx in (x0 + 11, x1 - 11) for fy in (y0 + 11, y1 - 11)]
            dock = g.difference(dock, feet)
        dock = g.largest(dock)

        design = Design(self.name, p, dock, ghosts=[Placed(ref.name, ref.id, box)], references=[ref])
        design.checks += self._checks(p, ref, dock, box, t)
        design.notes += [
            f"Pocket {bx + 2 * c:.2f} x {by + 2 * c:.2f} mm for a {bx:g} x {by:g} mm base ({ref.confidence}).",
            "Stick four 10 mm silicone bumpers into the recesses; they are what stops it sliding.",
            "PLA is fine for 70% ethanol wipe-downs; it is not autoclavable (softens near 60 C).",
        ]
        if "opentrons" in ref.id:
            design.notes.append("The Opentrons size is the rack base on a robot deck. A bench box with a lid "
                                "or skirt can be wider: measure yours and add it as a measured reference.")
        return design

    def _checks(self, p, ref, dock, box, t) -> list[Check]:
        checks = []
        lo, hi = box.bounds
        top = float(hi[2])
        checks.append(Check("box top above the bench", None if not p["max_height"] else top <= p["max_height"],
                            f"{top:.1f} mm", "highest point of the box (tips included) when docked"))
        footprint = dock.bounds
        centre = box.center_mass
        margin = min(centre[0] - footprint[0][0], footprint[1][0] - centre[0],
                     centre[1] - footprint[0][1], footprint[1][1] - centre[1])
        checks.append(Check("box centre of mass over the dock's base", margin > 10, f"{margin:.1f} mm inside the edge",
                            "projection of the box's centre (uniform-density assumption) onto the bench",
                            basis="ESTIMATED"))
        need = math.tan(math.radians(t))
        checks.append(Check("grip needed against a straight press on the tips", need < 0.5,
                            f"friction coefficient {need:.2f}",
                            "a press square to the tilted rack pushes the dock along the bench by tan(tilt) of the "
                            "force; stick-on silicone bumpers typically give 0.5 or more",
                            basis="ESTIMATED"))
        return checks


def _tilt(deg: float, lift: float) -> np.ndarray:
    """Rotate about the x axis so the back rises, then lift."""
    a = math.radians(deg)
    m = np.eye(4)
    m[1, 1], m[1, 2] = math.cos(a), -math.sin(a)
    m[2, 1], m[2, 2] = math.sin(a), math.cos(a)
    m[2, 3] = lift
    return m
