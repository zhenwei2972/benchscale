"""Export a shake_fill_rack's parts, one tip and a layout file, for the how-to animation.

Every mesh comes from the template itself, in the frame it is used in (the
stand's frame: the deck rests at z = stand height, the lid on the stand's
band), so the animation is at true scale.
Run:  python tools/export_video_assets.py OUT_DIR [name=value ...]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from benchscale.ghosts import pipette_tip
from benchscale.references import Library
from benchscale.templates import registry
from benchscale.templates.shake_fill_rack import BORDER, OVERLAP


def main(out: Path, given: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    lib, t = Library(), registry()["shake_fill_rack"]
    built = {}
    for piece in ("deck", "stand", "lid"):
        p = t.resolve({**given, "piece": piece}, lib)
        built[piece] = t.build(p, lib)
        built[piece].part.export(out / f"{piece}.stl")
    q = built["deck"].params
    pitch, rows, cols = q["pitch"], q["rows"], q["cols"]
    L, collar, ch, body, floor = q["tip_length"], q["collar_od"], q["collar_h"], q["body_od"], q["floor"]
    pipette_tip(L, collar, ch, body, 0.8).export(out / "tip.stl")

    reach = pitch / math.sqrt(2)
    edge = reach + 0.05
    D = (rows - 1) * pitch + 2 * edge
    pocket = collar + 0.6
    T = floor + q["pocket_depth"] + (reach - (pocket + q["hole_comp"]) / 2) * math.tan(math.radians(q["funnel_angle"]))
    Hs = L - ch - floor + 4.0
    z_top = Hs + T + BORDER
    holes = [round(q["hole"] + (c - (cols - 1) / 2) * q["hole_step"], 2) for c in range(cols)]
    layout = {
        "rows": rows, "cols": cols, "pitch": pitch, "holes": holes,
        "centres": [[edge + i * pitch, D - edge - j * pitch, i, j] for j in range(rows) for i in range(cols)],
        "stand_height": Hs, "deck_peaks": T, "rim_top": z_top, "lid_seat": z_top - OVERLAP,
        "tip": {"length": L, "collar_od": collar, "collar_h": ch, "body_od": body, "floor": floor},
        "seated_point_z": Hs + floor - (L - ch),
        "bounds": {k: built[k].part.bounds.tolist() for k in built},
        "tip_reference": built["deck"].references[0].name,
        "tip_confidence": built["deck"].references[0].confidence,
    }
    (out / "layout.json").write_text(json.dumps(layout, indent=1))
    print(out / "layout.json")


if __name__ == "__main__":
    args = dict(a.split("=", 1) for a in sys.argv[2:])
    main(Path(sys.argv[1]), args)
