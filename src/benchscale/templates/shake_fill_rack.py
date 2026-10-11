"""A tip rack that fills itself: shake loose bulk tips over it and they drop in point first.

Bulk tips cost about half as much as racked ones, but racking them by hand is
slow, and the printable loaders people share (funnels over an empty box, comb
sorters) need a hand-fix pass afterwards. Their two failure modes decide this
design:

* Upside-down tips. A funnel that passes the whole tip into a box below lets a
  tip in collar-first. Here every hole is narrower than the collar: a tip can
  only enter point first, and hangs by its collar. Upside down cannot happen.
* Tips stacked inside each other. Once a box position is filled, a funnel
  above it steers the next tip's point straight into the seated tip's open
  top. Here a filled position's collar stands above the funnels, so a full
  hole is a bump and an empty hole is a dip: loose tips slide off the full
  ones and fall into the empty ones.

The funnels overlap like an egg crate, so there is no flat land where a tip
can lie still: wherever a point touches the deck, it slides towards a hole.

Three parts, each printed flat without support: the deck, a stand that holds
it at the height the tips hang, and a lid to hold on while shaking.
"""

from __future__ import annotations

import math

import numpy as np
import trimesh

from .. import geometry as g
from ..ghosts import pipette_tip
from ..printers import PRINTERS
from ..references import Library
from . import Check, Design, Param, Placed, Template

PIECES = ["set", "deck", "stand", "lid"]
CLEAR = 0.3           # deck in the stand, per side
LID_CLEAR = 0.4       # lid over the stand, per side
LEDGE = 2.0           # how far the stand's ledge reaches under the deck
OVERLAP = 8.0         # how far the lid comes down over the stand
BENCH_GAP = 4.0       # tip points above the bench
KEY = 3.0             # chamfered corner (behind A1) so the deck only fits one way
BORDER = 2.0          # the deck's edge rises this far above the funnel peaks, still sloping inwards


def _ring(outer, inner, z0, z1):
    return g.extrude(g.clean(outer.difference(inner)), z0, z1)


def _stepped_ring(outline, reach: float, z_top: float, outward: bool, step: float = 0.5):
    """A ledge that grows by `reach` towards its top in 0.5 mm steps: a 45 degree overhang, printable."""
    parts, n = [], max(1, int(round(reach / step)))
    for k in range(1, n + 1):
        w = reach * k / n
        z0 = z_top - reach + (k - 1) * reach / n
        # 0.05 mm into the wall it hangs from: faces that only touch do not fuse
        if outward:
            ring = outline.buffer(w, join_style=2).difference(outline.buffer(-0.05, join_style=2))
        else:
            ring = outline.buffer(0.05, join_style=2).difference(outline.buffer(-w, join_style=2))
        parts.append(g.extrude(g.clean(ring), z0, z_top))
    return parts


class ShakeFillRack(Template):
    name = "shake_fill_rack"
    title = "Shake-fill tip rack"
    summary = ("A 96-position tip rack that loads itself from loose bulk tips: pour some on, hold the lid on, "
               "shake, and they drop in point first. Deck + stand + lid, each printed flat. Try rows=3 cols=4 "
               "hole_step=0.3 first: a 12-position coupon that finds the right hole for your tips.")
    params = [
        Param("tip", "reference", "std:axygen_t200y_tip", "The pipette tip (reference id)."),
        Param("piece", "choice", "set", "set (every part, laid out to print together), deck, stand or lid.",
              choices=PIECES),
        Param("rows", "int", 8, "Rows (A-H).", "", 1, 8),
        Param("cols", "int", 12, "Columns (1-12).", "", 1, 12),
        Param("pitch", "float", 9.0, "Centre spacing. 9.0 is the 96 format, which multichannel pipettes need.",
              "mm", 7.0, 15.0),
        Param("collar_od", "float", 0.0, "Your tip's widest (collar) diameter; 0 = from the reference.", "mm", 0.0, 15.0),
        Param("body_od", "float", 0.0, "Tip diameter just below the collar; 0 = from the reference.", "mm", 0.0, 15.0),
        Param("collar_h", "float", 0.0, "Top of the tip down to the shoulder it hangs by; 0 = from the reference.",
              "mm", 0.0, 30.0),
        Param("tip_length", "float", 0.0, "Overall tip length; 0 = from the reference.", "mm", 0.0, 120.0),
        Param("hole", "float", 0.0, "Hole the tip hangs in; 0 = body + 0.5 mm (and below the collar).", "mm", 0.0, 15.0),
        Param("hole_step", "float", 0.0, "Change the hole by this much per column - for a test coupon.", "mm", 0.0, 1.0),
        Param("hole_comp", "float", 0.15, "Added to every hole and pocket, because printed holes come out small.",
              "mm", 0.0, 0.5),
        Param("pocket_depth", "float", 1.0, "Recess that centres the collar.", "mm", 0.4, 3.0),
        Param("funnel_angle", "float", 45.0, "Funnel slope from horizontal.", "deg", 30.0, 60.0),
        Param("floor", "float", 1.6, "Deck under the collar.", "mm", 1.0, 4.0),
        Param("wall", "float", 1.6, "Stand and lid wall.", "mm", 1.2, 4.0),
        Param("headroom", "float", 30.0, "Room under the lid for loose tips to tumble.", "mm", 15.0, 60.0),
    ]

    def build(self, p: dict, lib: Library) -> Design:
        ref = lib.get(p["tip"])
        f = ref.features
        collar = p["collar_od"] or f.get("collar_od") or ref.d
        body = p["body_od"] or f.get("body_od") or round(collar * 0.8, 2)
        collar_h = p["collar_h"] or f.get("collar_h") or 7.0
        length = p["tip_length"] or ref.h
        point = min(f.get("point_od", 0.8), body)
        if body > collar - 0.6:
            raise ValueError(f"body {body:g} mm is too close to the collar {collar:g} mm: the tip needs a "
                             "shoulder at least 0.3 mm wide per side to hang by")
        rows, cols, pitch = p["rows"], p["cols"], p["pitch"]
        hole = p["hole"] or round(min(body + 0.5, collar - 0.6), 2)
        holes = [round(hole + (c - (cols - 1) / 2) * p["hole_step"], 2) for c in range(cols)]
        comp, floor, pd, wall = p["hole_comp"], p["floor"], p["pocket_depth"], p["wall"]
        pocket = round(collar + 0.6, 2)
        t = math.tan(math.radians(p["funnel_angle"]))
        reach = pitch / math.sqrt(2)                 # funnels meet at the diagonal: no flat land between them
        fd = (reach - (pocket + comp) / 2) * t
        T = floor + pd + fd                          # funnel peaks; the edges rise to T + BORDER
        edge = reach + 0.05
        W, D = (cols - 1) * pitch + 2 * edge, (rows - 1) * pitch + 2 * edge
        Hs = round(length - collar_h - floor + BENCH_GAP, 2)   # deck underside above the bench
        hang = length - collar_h - floor                       # tip below the deck underside

        # --- deck --------------------------------------------------------------------------
        outline = g.rounded_rect(0, 0, W, D, 2.0)
        key = g.Polygon([(0, D), (KEY, D), (0, D - KEY)])      # behind A1 (back left)
        outline = g.clean(outline.difference(key.buffer(0.01)))
        centres = [(edge + i * pitch, D - edge - j * pitch, i, j) for j in range(rows) for i in range(cols)]
        cutters = []
        for x, y, i, _ in centres:
            hr, pr, top = (holes[i] + comp) / 2, (pocket + comp) / 2, T + BORDER + 1.0
            profile = np.array([[0, -1], [hr, -1], [hr, floor], [pr, floor], [pr, floor + pd],
                                [pr + (top - floor - pd) / t, top], [0, top]])
            cutter = trimesh.creation.revolve(profile, sections=48)
            cutter.apply_translation((x, y, 0.0))
            cutters.append(cutter)
        deck = g.difference(g.extrude(outline, 0.0, T + BORDER), cutters)

        # --- stand -------------------------------------------------------------------------
        rim_in = outline.buffer(CLEAR, join_style=2)
        rim_out = rim_in.buffer(wall, join_style=2)
        z_top = Hs + T + BORDER
        parts = [_ring(rim_out, rim_in, 0.0, z_top)]
        parts += _stepped_ring(rim_in, LEDGE, Hs, outward=False)               # the deck sits on this
        z_band = z_top - OVERLAP                                              # the lid sits on this
        band = wall + LID_CLEAR
        parts += _stepped_ring(rim_out, band, z_band, outward=True)
        ribs = []
        if D > 60 and rows >= 2:
            y = D - edge - (rows // 2 - 0.5) * pitch
            ribs.append(g.extrude(g.rect(-CLEAR - 0.5, y - 0.8, W + CLEAR + 0.5, y + 0.8), 0.0, Hs))
        if W > 60 and cols >= 2:
            x = edge + (cols // 2 - 0.5) * pitch
            ribs.append(g.extrude(g.rect(x - 0.8, -CLEAR - 0.5, x + 0.8, D + CLEAR + 0.5), 0.0, Hs))
        stand = g.union(parts + ribs)
        windows = []
        if Hs > 30 and W > 50:                      # see the tips, save plastic
            win = g.stadium(W / 2, Hs / 2 - 1, W - 28, Hs - 18)
            for y0 in (-CLEAR - wall - 1, D + CLEAR - 1):
                windows.append(g.extrude_xz(win, y0, y0 + wall + 2))
        if p["hole_step"] and cols > 1:            # column marks for a coupon: 1, 2, 3... dots on the front
            for i in range(cols):
                x = edge + i * pitch
                for k in range(i + 1):
                    dot = g.cylinder(1.4, 0, 1.0, sections=16)
                    dot = g.rotate_x(dot, 90.0)
                    dot.apply_translation((x, -CLEAR - wall + 0.6, z_band - 4.0 - 2.4 * k))
                    windows.append(dot)
        if windows:
            stand = g.difference(stand, windows)

        # --- lid ---------------------------------------------------------------------------
        lid_in = rim_out.buffer(LID_CLEAR, join_style=2)
        lid_out = lid_in.buffer(wall, join_style=2)
        lid_h = OVERLAP + p["headroom"] + 1.2
        lid = g.union([_ring(lid_out, lid_in, 0.0, lid_h - 1.15), g.extrude(lid_out, lid_h - 1.2, lid_h)])

        # --- tips, hanging where they will hang ------------------------------------------
        def tips_at(z_deck: float) -> trimesh.Trimesh:
            one = pipette_tip(length, collar, collar_h, body, point)
            many = []
            for x, y, _, _ in centres:
                m = one.copy()
                m.apply_translation((x, y, z_deck + floor - (length - collar_h)))
                many.append(m)
            return trimesh.util.concatenate(many)

        piece = p["piece"]
        lid_print = g.rotate_x(lid, 180.0)
        lid_print.apply_translation(-lid_print.bounds[0])
        if piece == "deck":
            part, printed, ghosts, n = deck, None, [tips_at(0.0)], 1
        elif piece == "stand":
            part, printed, ghosts, n = stand, None, [tips_at(Hs)], 1
        elif piece == "lid":
            part, printed, ghosts, n = lid, lid_print, [], 1
        else:
            seated = deck.copy()
            seated.apply_translation((0, 0, Hs))
            beside = lid.copy()
            beside.apply_translation((W + 2 * wall + 25 - lid.bounds[0][0], 0, 0))
            part = trimesh.util.concatenate([stand, seated, beside])
            printed = self._layout([stand, deck, lid_print])
            ghosts, n = [tips_at(Hs)], 3

        design = Design(self.name, {**p, "hole": hole, "collar_od": collar, "body_od": body, "collar_h": collar_h,
                                    "tip_length": length},
                        part, print_part=printed, pieces=n, references=[ref],
                        ghosts=[Placed(f"{rows * cols} x {ref.name}", ref.id, m) for m in ghosts])

        # --- checks: each one is computed from the geometry above -------------------------
        if p["hole_step"]:
            # A coupon brackets the estimate on purpose: report each column instead of failing.
            fits = [i + 1 for i, h in enumerate(holes) if collar - h >= 0.3 and h - body >= 0.2]
            design.checks.append(Check(
                "coupon columns that suit the estimated tip", None,
                f"columns {fits} of {cols}" if fits else "none",
                f"hang needs hole <= collar - 0.3 ({collar - 0.3:.2f}), slide needs hole >= body + 0.2 "
                f"({body + 0.2:.2f}); your real tips decide", basis="ESTIMATED"))
        else:
            big, small = max(holes), min(holes)
            design.checks.append(Check(
                "a tip cannot go in upside down", collar - big >= 0.3,
                f"collar {collar:g} mm, largest hole {big:g} mm: {collar - big:.2f} mm to spare",
                "the hole must be narrower than the collar so only the point fits"))
            design.checks.append(Check(
                "the tip's body slides into the hole", small - body >= 0.2,
                f"body {body:g} mm, smallest hole {small:g} mm: {small - body:.2f} mm clearance"))
        proud = floor + collar_h - T
        design.checks.append(Check(
            "filled holes stand above the funnels", proud >= 2.0,
            f"collar top {proud:.1f} mm above the funnel peaks",
            "so a loose tip slides off a filled hole instead of stacking into the seated tip"))
        tri = deck.triangles_center
        up = (deck.face_normals[:, 2] > 0.985) & (tri[:, 2] > floor + 0.05)
        flat = float(deck.area_faces[up].sum()) / outline.area
        design.checks.append(Check(
            "no flat land between funnels", flat < 0.05, f"{100 * flat:.1f}% of the deck top is flat",
            "flat land is where loose tips lie still instead of finding a hole"))
        web = pitch - (pocket + comp)
        design.checks.append(Check("wall between neighbouring pockets", web >= 0.8, f"{web:.2f} mm",
                                   "two 0.4 mm lines at least"))
        design.checks.append(Check("tip points clear the bench", Hs - hang >= 3.0,
                                   f"{Hs - hang:.1f} mm under the lowest point"))
        play = (pocket + comp - collar) / 2
        design.checks.append(Check(
            "tips sit on the 9 mm grid for a multichannel", None, f"+/-{play:.2f} mm sideways play at the collar",
            f"printed pockets usually come out about {comp:g} mm small, which tightens this", basis="ESTIMATED"))
        if piece == "set":
            bed = PRINTERS["bambu_a1_mini"]
            design.checks.append(Check(
                "parts fit one A1 mini plate together", printed.bounding_box.extents[0] <= bed["x"] - 4
                and printed.bounding_box.extents[1] <= bed["y"] - 4,
                "{:.0f} x {:.0f} mm laid out".format(*printed.bounding_box.extents[:2]),
                "if not, print piece=deck, piece=stand and piece=lid one at a time"))

        # --- what a person needs to know --------------------------------------------------
        sizes = ", ".join(f"col {i + 1}: {h:g}" for i, h in enumerate(holes)) if p["hole_step"] else f"{hole:g}"
        design.notes += [
            f"Built for {ref.name} ({ref.confidence}): collar {collar:g} mm, body {body:g} mm, "
            f"collar length {collar_h:g} mm, length {length:g} mm.",
            f"Hole sizes (mm): {sizes}. Modelled {comp:g} mm larger to allow for printing.",
            "Load: pour in about 1.5x as many tips as there are holes, put the lid on, shake side to side "
            "for 10-20 s, lift the lid, tilt the rack (do not turn it over) to pour the extras back.",
            "Pick out any tip that stands higher than its neighbours; fill the last few holes by hand.",
            f"Deck sits in the stand one way only (the cut corner is behind A1). Stand height {Hs:.1f} mm "
            f"puts the tip points {BENCH_GAP:g} mm above the bench.",
            "PLA is not autoclavable (it softens near 60 C): use it for non-sterile tips such as T-200-Y.",
        ]
        if p["hole_step"]:
            design.notes.append("Coupon: the stand's front has 1, 2, 3... dots under each column. The right hole "
                                "holds a tip upright with its collar down in the pocket; too small and it sits "
                                "high or tilted, too big and it wobbles or the shoulder slips in.")
        return design

    @staticmethod
    def _layout(meshes: list[trimesh.Trimesh], gap: float = 6.0) -> trimesh.Trimesh:
        """Lay the parts out on the plate in a row, wrapping to a second row if needed."""
        bed = PRINTERS["bambu_a1_mini"]
        placed, x, y, row_d = [], 0.0, 0.0, 0.0
        for m in meshes:
            m = m.copy()
            m.apply_translation(-m.bounds[0])
            ex = m.bounding_box.extents
            if x > 0 and x + ex[0] > bed["x"] - 4:
                x, y, row_d = 0.0, y + row_d + gap, 0.0
            m.apply_translation((x, y, 0.0))
            placed.append(m)
            x += ex[0] + gap
            row_d = max(row_d, ex[1])
        return trimesh.util.concatenate(placed)
