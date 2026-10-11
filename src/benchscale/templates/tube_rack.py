"""A rack for tubes: a perforated deck on two walls.

The same proven layout as prompt-to-bench's conical rack (a plate on two long
walls, printed upside down so nothing needs support), generalised to any tube
in the reference library: hole size, pitch and deck height all follow from the
tube's real diameter and length.
"""

from __future__ import annotations

from .. import geometry as g
from ..ghosts import ghost
from ..references import Library
from . import Check, Design, Param, Placed, Template


class TubeRack(Template):
    name = "tube_rack"
    title = "Tube rack"
    summary = ("A perforated deck on two walls for any tube (Falcon 15/50 mL, 1.5 mL, test tubes, or a "
               "measured one). Prints upside down without supports; tubes stand on the bench.")
    params = [
        Param("tube", "reference", "std:falcon_50ml", "The tube - a reference id from search_references, or a measured one."),
        Param("rows", "int", 2, "Rows of tubes (front to back).", "", 1, 12),
        Param("cols", "int", 3, "Columns of tubes (left to right).", "", 1, 16),
        Param("clearance", "float", 0.5, "Gap between tube and hole, per side.", "mm", 0.2, 2.0),
        Param("pitch", "float", 0.0, "Centre-to-centre spacing. 0 = tube diameter + 25% (at least 4 mm web).", "mm", 0.0, 100.0),
        Param("deck", "float", 4.0, "Deck (plate) thickness.", "mm", 2.0, 10.0),
        Param("wall", "float", 4.0, "Wall thickness.", "mm", 2.0, 10.0),
        Param("height", "float", 0.0, "Deck height above the bench. 0 = 60% of the tube length.", "mm", 0.0, 250.0),
    ]

    def build(self, p: dict, lib: Library) -> Design:
        ref = lib.get(p["tube"])
        if ref.shape != "cylinder":
            raise ValueError(f"{ref.name} is a box; use tip_box_dock or holder for boxes")
        d, c = ref.d, p["clearance"]
        hole = d + 2 * c
        pitch = p["pitch"] or max(d * 1.25, hole + 4.0)
        if pitch - hole < 1.6:
            raise ValueError(f"pitch {pitch:g} mm leaves {pitch - hole:.1f} mm between holes; need 1.6 mm")
        rows, cols, wall, deck = p["rows"], p["cols"], p["wall"], p["deck"]
        H = p["height"] or round(0.6 * ref.h, 1)
        margin = max(5.0, pitch - hole)
        W = cols * pitch + 2 * margin - (pitch - hole)
        D = rows * pitch + 2 * margin - (pitch - hole)

        plate = g.bevelled_slab(g.rounded_rect(0, 0, W, D, 3.0), H - deck, H, top_bevel=0.6)
        walls = [g.extrude(g.rounded_rect(x0, 0, x0 + wall, D, 1.0), 0.0, H - deck + 0.01)
                 for x0 in (0.0, W - wall)]
        # a window in each wall: lighter, and you can see the tube tips
        if H - deck > 25 and D > 40:
            window = g.stadium(D / 2, (H - deck) / 2, D - 24, (H - deck) - 18)
            walls = [g.difference(wl, [g.extrude_yz(window, x0 - 1, x0 + wall + 1)])
                     for wl, x0 in zip(walls, (0.0, W - wall))]
        rack = g.union([plate, *walls])
        holes, tubes = [], []
        for i in range(cols):
            for j in range(rows):
                cx = margin + hole / 2 + i * pitch
                cy = margin + hole / 2 + j * pitch
                holes.append(g.cylinder(hole, H - deck - 1, H + 1, cx, cy))
                holes += g.lead_in(g.Point(cx, cy).buffer(hole / 2, quad_segs=24), H, 0.6)
                tube = ghost(ref)
                tube.apply_translation((cx, cy, 0.0))
                tubes.append(tube)
        rack = g.largest(g.difference(rack, holes))

        flipped = g.rotate_x(rack, 180.0)
        flipped.apply_translation(-flipped.bounds[0])
        design = Design(self.name, {**p, "pitch": pitch, "height": H}, rack, print_part=flipped,
                        ghosts=[Placed(f"{ref.name} #{k + 1}", ref.id, m) for k, m in enumerate(tubes)],
                        references=[ref])
        above = ref.h - H
        design.checks.append(Check("tube above the deck", above >= 15, f"{above:.1f} mm",
                                   "length of tube you can grab above the deck"))
        design.checks.append(Check("web between holes", pitch - hole >= 1.6, f"{pitch - hole:.1f} mm"))
        design.notes += [f"Holes {hole:.1f} mm for a {d:g} mm tube ({ref.confidence}).",
                         "Prints upside down (deck on the plate); flip it after printing."]
        return design
