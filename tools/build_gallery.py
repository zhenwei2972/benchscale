"""Build the static design gallery in docs/ (served by GitHub Pages).

Every design is built fresh from its template, so the files, checks and notes
on the page are the same ones benchscale produces locally.
Run:  python tools/build_gallery.py
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import trimesh

from benchscale import design

DOCS = Path(__file__).resolve().parent.parent / "docs"
OUT = DOCS / "gallery"
REPO = "https://github.com/zhenwei2972/benchscale"

# Slicer figures are Bambu Studio's own estimates (A1 mini, 0.2 mm layers, 15% infill), taken when each
# file was sliced; they are labelled ESTIMATED on the page.
GALLERY = [
    {"slug": "shake-fill-rack", "title": "Shake-fill tip rack (96)",
     "blurb": "Loads itself from bulk 200 uL tips: pour, shake, done. Holes narrower than the collar stop "
              "upside-down tips; filled holes stand proud so tips don't stack.",
     "status": "Designed. Not printed at full size yet.",
     "template": "shake_fill_rack", "params": {"piece": "set"},
     "parts": [("Deck", {"piece": "deck"}, "1 h 21 min, 19.9 g"), ("Stand", {"piece": "stand"}, "1 h 24 min, 48.7 g"),
               ("Lid", {"piece": "lid"}, "1 h 05 min, 43.0 g")],
     "video": "shake_fill_howto.mp4"},
    {"slug": "shake-fill-coupon", "title": "Shake-fill test coupon (12)",
     "blurb": "Three-part, 12-hole test set with four hole sizes (5.65 to 6.55 mm) to find the right fit for "
              "your tips before printing the full rack.",
     "status": "Printed 11 Oct 2026 (68 min). Fit test with real tips pending.",
     "template": "shake_fill_rack", "params": {"rows": 3, "cols": 4, "hole_step": 0.3},
     "parts": [("All three parts, one plate", {"rows": 3, "cols": 4, "hole_step": 0.3}, "1 h 12 min, 32.9 g")],
     "video": "shake_fill_howto.mp4"},
    {"slug": "tip-box-dock", "title": "Tilted tip-box dock",
     "blurb": "Holds a TipOne 200 uL rack tilted 15 degrees toward you so it can't slide in the biosafety "
              "cabinet; finger notches and recesses for rubber feet.",
     "status": "Designed. Not printed yet.",
     "template": "tip_box_dock",
     "params": {"box": "opentrons:tipone_96_tiprack_200ul", "tilt_deg": 15, "finger_notches": True,
                "feet": True, "max_height": 120},
     "parts": [("Dock", None, "2 h 31 min, 72.9 g")]},
    {"slug": "falcon-rack", "title": "Falcon 50 mL rack",
     "blurb": "Six 50 mL conical tubes in a 2 x 3 rack that prints upside down without supports.",
     "status": "Designed. Not printed yet.",
     "template": "tube_rack", "params": {"tube": "std:falcon_50ml", "rows": 2, "cols": 3},
     "parts": [("Rack", None, None)]},
    {"slug": "slide-holder", "title": "Microscope slide holder",
     "blurb": "A pocket for a standard 25 x 75 mm slide, with a lead-in and a finger notch.",
     "status": "Designed. Not printed yet.",
     "template": "holder", "params": {"object": "std:microscope_slide"},
     "parts": [("Holder", None, None)]},
]


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for g in GALLERY:
            folder = OUT / g["slug"]
            folder.mkdir(exist_ok=True)
            res = design.run(g["template"], dict(g["params"]), out_root=root)
            src = Path(res["folder"])
            shutil.copy(src / "part.stl", folder / "view.stl")
            ghosts = [trimesh.load(src / gh["file"]) for gh in res["ghosts"]]
            if ghosts:
                trimesh.util.concatenate(ghosts).export(folder / "holds.stl")
            downloads, part_fits = [], []
            for i, (label, params, estimate) in enumerate(g["parts"]):
                if params is None:
                    path = src / "print.stl"
                else:
                    part_res = design.run(g["template"], params, out_root=root)
                    path = Path(part_res["folder"]) / "print.stl"
                    part_fits.append((label, next(c for c in part_res["checks"] if c["name"].startswith("fits the"))))
                name = f"{g['slug']}-{i + 1}.stl" if len(g["parts"]) > 1 else f"{g['slug']}.stl"
                shutil.copy(path, folder / name)
                downloads.append({"label": label, "file": f"gallery/{g['slug']}/{name}", "estimate": estimate,
                                  "kb": round((folder / name).stat().st_size / 1024)})
            checks = res["checks"]
            if len(part_fits) > 1:   # a multi-part set: report each printed part's fit, not the laid-out set
                checks = [c for c in checks if not (c["name"].startswith("fits the") or "one A1 mini plate" in c["name"])]
                checks.insert(1, {"name": "each part fits the A1 mini on its own",
                                  "ok": all(c["ok"] for _, c in part_fits),
                                  "value": "; ".join(f"{lbl} {c['value']}" for lbl, c in part_fits),
                                  "detail": "printed one part at a time", "basis": "computed from the model"})
            entries.append({
                "slug": g["slug"], "title": g["title"], "blurb": g["blurb"], "status": g["status"],
                "template": g["template"], "size_mm": res["size_mm"], "params": res["params"],
                "checks": checks, "notes": res["notes"], "references": res["references"],
                "view": f"gallery/{g['slug']}/view.stl",
                "holds": f"gallery/{g['slug']}/holds.stl" if ghosts else None,
                "downloads": downloads, "video": g.get("video"),
                "rebuild": "benchscale design " + g["template"] + "".join(
                    f" -p {k}={v}" for k, v in g["params"].items()),
            })
    (OUT / "designs.json").write_text(json.dumps({"repo": REPO, "designs": entries}, indent=1, default=str))
    (DOCS / ".nojekyll").write_text("")
    print(f"{len(entries)} designs -> {OUT}")


if __name__ == "__main__":
    build()
