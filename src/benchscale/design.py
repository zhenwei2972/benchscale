"""Run a template, check the result, and save everything the viewer and printer need."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import trimesh

from . import geometry as g
from .printers import DEFAULT_PRINTER, PRINTERS
from .references import Library, state_dir
from .templates import Check, Design, registry

PLA_G_PER_CM3 = 1.24


def designs_dir() -> Path:
    path = state_dir() / "designs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def common_checks(design: Design, printer: str) -> list[Check]:
    part = design.part
    pp = design.print_part or part
    n = len(part.split(only_watertight=False))
    label = "one closed solid" if design.pieces == 1 else f"{design.pieces} closed solids, one per part"
    checks = [Check(label, part.is_watertight and n == design.pieces,
                    f"watertight={part.is_watertight}, pieces={n}")]
    bed = PRINTERS[printer]
    ex = sorted(pp.bounding_box.extents[:2])
    fits = ex[0] <= min(bed["x"], bed["y"]) - 4 and ex[1] <= max(bed["x"], bed["y"]) - 4 and pp.bounding_box.extents[2] <= bed["z"]
    checks.append(Check(f"fits the {bed['name']}", fits,
                        f"{pp.bounding_box.extents[0]:.1f} x {pp.bounding_box.extents[1]:.1f} x {pp.bounding_box.extents[2]:.1f} mm",
                        f"build volume {bed['x']} x {bed['y']} x {bed['z']} mm, 2 mm margin each side"))
    worst = max((g.overlap_mm3(part, gh.mesh) for gh in design.ghosts), default=0.0)
    checks.append(Check("reference objects fit without touching the walls", worst < 0.5,
                        f"overlap {worst:.3f} mm3",
                        "each reference object, placed where it sits, intersected with the part"))
    vol = abs(part.volume) / 1000
    checks.append(Check("plastic, solid upper bound", None, f"{vol:.1f} cm3 = {vol * PLA_G_PER_CM3:.0f} g PLA",
                        "a slicer's sparse infill uses roughly a third to a half of this", basis="ESTIMATED"))
    return checks


def run(template: str, params: dict | None = None, printer: str = DEFAULT_PRINTER,
        lib: Library | None = None, out_root: Path | None = None) -> dict:
    lib = lib or Library()
    templates = registry()
    if template not in templates:
        raise ValueError(f"unknown template {template!r}; choose from {sorted(templates)}")
    if printer not in PRINTERS:
        raise ValueError(f"unknown printer {printer!r}; choose from {sorted(PRINTERS)}")
    t = templates[template]
    resolved = t.resolve(params or {}, lib)
    design = t.build(resolved, lib)
    design.checks = common_checks(design, printer) + design.checks
    return export(design, printer, out_root or designs_dir())


def export(design: Design, printer: str, root: Path) -> dict:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", design.template)
    folder = root / f"{stamp}-{slug}"
    n = 1
    while folder.exists():
        n += 1
        folder = root / f"{stamp}-{slug}-{n}"
    folder.mkdir(parents=True)
    design.part.export(folder / "part.stl")
    (design.print_part or design.part).export(folder / "print.stl")
    ghosts = []
    for i, gh in enumerate(design.ghosts):
        name = f"ghost_{i}.stl"
        gh.mesh.export(folder / name)
        ghosts.append({"name": gh.name, "ref_id": gh.ref_id, "file": name})
    ext = design.part.bounding_box.extents
    scene = {
        "id": folder.name, "template": design.template, "params": design.params, "printer": printer,
        "part": "part.stl", "print_file": "print.stl", "ghosts": ghosts,
        "size_mm": [round(float(v), 2) for v in ext],
        "checks": [c.to_dict() for c in design.checks],
        "notes": design.notes,
        "references": [{**r.summary(), "url": r.url, "license": r.license, "notes": r.notes} for r in design.references],
    }
    (folder / "scene.json").write_text(json.dumps(scene, indent=1, default=str))
    (root / "latest.json").write_text(json.dumps({"id": folder.name}))
    return {"design_id": folder.name, "folder": str(folder), "files": {
        "part_stl": str(folder / "part.stl"), "print_stl": str(folder / "print.stl")}, **scene}


def load_scene(design_id: str | None = None, root: Path | None = None) -> dict:
    root = root or designs_dir()
    if not design_id:
        latest = root / "latest.json"
        if not latest.exists():
            raise FileNotFoundError("no designs yet")
        design_id = json.loads(latest.read_text())["id"]
    return json.loads((root / design_id / "scene.json").read_text())


def mesh_of(design_id: str, name: str, root: Path | None = None) -> trimesh.Trimesh:
    return trimesh.load((root or designs_dir()) / design_id / name)
