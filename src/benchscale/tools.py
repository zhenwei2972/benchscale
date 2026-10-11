"""The operations a chat model (or a person) uses to design at real scale.

One set of plain functions, shared by the MCP server, the built-in chat and the
command line, so every surface behaves the same. Every return value is JSON.
"""

from __future__ import annotations

import os

from . import bases, design
from .printers import DEFAULT_PRINTER, PRINTERS
from .references import Library
from .templates import Check, Design, Placed, registry

_lib: Library | None = None


def library() -> Library:
    global _lib
    if _lib is None:
        _lib = Library()
    return _lib


def viewer_url(design_id: str | None = None) -> str:
    port = os.environ.get("BENCHSCALE_PORT", "8742")
    return f"http://localhost:{port}/" + (f"?design={design_id}" if design_id else "")


def search_references(query: str, kind: str | None = None, limit: int = 8) -> dict:
    """Find real objects by name: 'falcon 50 ml', 'eppendorf 1000 tip rack', '96 well plate', 'slide'.
    kind narrows it: tip_rack, plate, tube, tube_rack, reservoir, slide, block, adapter."""
    hits = library().search(query, kind=kind, limit=limit)
    return {"query": query, "results": [h.summary() for h in hits],
            "hint": "Sizes are real. If the user has the object in hand, ask them to measure it and "
                    "save it with add_measured_reference - measured sizes win."}


def get_reference(ref_id: str, include_wells: bool = False) -> dict:
    """Full detail for one reference: size, features, where the numbers come from, licence."""
    return library().get(ref_id).to_dict(wells=include_wells)


def add_measured_reference(name: str, kind: str, shape: str, x: float = 0, y: float = 0, z: float = 0,
                           d: float = 0, h: float = 0, notes: str = "") -> dict:
    """Save an object the user measured. shape 'box' takes x (width), y (depth), z (height);
    'cylinder' takes d (outside diameter) and h (height). All in mm. It is used ahead of library sizes."""
    ref = library().add_measured(name, kind, shape, notes, x=x, y=y, z=z, d=d, h=h)
    return {"saved": ref.summary()}


def list_templates() -> dict:
    """The part templates, each built around reference objects."""
    return {"templates": [{"name": t.name, "title": t.title, "summary": t.summary} for t in registry().values()]}


def describe_template(name: str) -> dict:
    """A template's parameters with units, defaults and limits."""
    templates = registry()
    if name not in templates:
        return {"error": f"unknown template {name!r}", "templates": sorted(templates)}
    return templates[name].describe()


def design_part(template: str, params: dict | None = None, printer: str = DEFAULT_PRINTER) -> dict:
    """Build a part from a template, around real reference objects, and check it.
    Returns the checks (each labelled computed or ESTIMATED), the size, the files and a viewer link."""
    try:
        result = design.run(template, params or {}, printer, lib=library())
    except (ValueError, KeyError) as exc:
        return {"error": str(exc), "hint": "describe_template lists valid parameters"}
    failed = [c["name"] for c in result["checks"] if c["ok"] is False]
    return {"design_id": result["design_id"], "viewer": viewer_url(result["design_id"]),
            "size_mm": result["size_mm"], "params": result["params"], "checks": result["checks"],
            "failed_checks": failed, "notes": result["notes"], "files": result["files"],
            "references": result["references"]}


def list_base_models(query: str = "") -> dict:
    """Free, openly licensed starting designs (Prompt to Bench, CERN-OHL-P-2.0)."""
    words = query.lower().split()
    out = []
    for e in bases.catalog():
        text = f"{e['id']} {e['name']} {e['description']}".lower()
        if all(w in text for w in words):
            out.append({k: e[k] for k in ("id", "name", "kind", "license")} | {"params": [p["name"] for p in e["params"]]})
    return {"base_models": out, "openscad_installed": bases.openscad() is not None}


def render_base_model(base_id: str, params: dict | None = None, printer: str = DEFAULT_PRINTER) -> dict:
    """Render a base model with chosen parameters (needs OpenSCAD) and check it like any design."""
    try:
        mesh = bases.render(base_id, params)
    except (KeyError, ValueError, RuntimeError) as exc:
        return {"error": str(exc)}
    entry = bases.find(base_id)
    d = Design(template=f"base:{entry['id']}", params=params or {}, part=mesh, notes=[
        f"Base model {entry['name']} from {entry['source']}, licence {entry['license']}."])
    d.checks = design.common_checks(d, printer)
    result = design.export(d, printer, design.designs_dir())
    return {"design_id": result["design_id"], "viewer": viewer_url(result["design_id"]),
            "size_mm": result["size_mm"], "checks": result["checks"], "files": result["files"]}


def printers() -> dict:
    """Printers whose build volume the checks know."""
    return {"printers": PRINTERS, "default": DEFAULT_PRINTER}


TOOLS = [search_references, get_reference, add_measured_reference, list_templates, describe_template,
         design_part, list_base_models, render_base_model, printers]

__all__ = [f.__name__ for f in TOOLS] + ["Check", "Placed"]
