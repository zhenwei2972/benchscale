"""Free, openly licensed base models to start from.

The Prompt to Bench library (CERN-OHL-P-2.0) ships 17 parametric OpenSCAD lab
designs - tube racks, a gel comb, a funnel, a micropestle, motor brackets.
They are included unmodified; this module lists them with their parameters and
renders them when OpenSCAD is installed.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import trimesh

ROOT = Path(__file__).parent / "data" / "bases" / "prompt-to-bench"
SOURCE = "Prompt to Bench (github.com/ATinyGreenCell/prompt-to-bench)"
LICENSE = "CERN-OHL-P-2.0"

_PARAM = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;]+);\s*(//\s*(.*))?$")


def openscad() -> str | None:
    found = shutil.which("openscad")
    if found:
        return found
    app = Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")
    return str(app) if app.exists() else None


def _parse(path: Path) -> dict:
    lines = path.read_text().splitlines()
    header = []
    for line in lines:
        if not line.startswith("//"):
            break
        header.append(line[2:].strip())
    params, comment, section, hidden = [], "", "", False
    for line in lines:
        s = line.strip()
        sec = re.match(r"/\*\s*\[(.+?)\]\s*\*/", s)
        if sec:
            section = sec.group(1)
            hidden = section.lower() == "hidden"
            continue
        if hidden or not section:
            comment = s[2:].strip() if s.startswith("//") else ""
            continue
        if s.startswith("//"):
            comment = s[2:].strip()
            continue
        m = _PARAM.match(s)
        if m:
            params.append({"name": m.group(1), "default": m.group(2).strip(),
                           "description": comment or (m.group(4) or "").strip(), "section": section})
        comment = ""
    kind = path.parent.name
    return {"id": f"p2b:{kind}/{path.stem}", "name": header[0] if header else path.stem, "kind": kind,
            "description": " ".join(header[1:]), "params": params, "file": str(path.relative_to(ROOT)),
            "source": SOURCE, "license": LICENSE}


def catalog() -> list[dict]:
    return [_parse(p) for p in sorted((ROOT / "designs").rglob("*.scad"))]


def find(base_id: str) -> dict:
    for entry in catalog():
        if entry["id"] == base_id or entry["id"].endswith(base_id):
            return entry
    raise KeyError(f"no base model {base_id!r}")


def render(base_id: str, params: dict | None = None) -> trimesh.Trimesh:
    exe = openscad()
    if not exe:
        raise RuntimeError("OpenSCAD is not installed, so base models cannot be rendered here. "
                           "Install it (macOS: brew install --cask openscad; others: openscad.org), "
                           "or use a native template instead.")
    entry = find(base_id)
    known = {p["name"] for p in entry["params"]}
    unknown = sorted(set(params or {}) - known)
    if unknown:
        raise ValueError(f"unknown parameter(s) {unknown} for {entry['id']}; it takes {sorted(known)}")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "part.stl"
        cmd = [exe, "-o", str(out)]
        for k, v in (params or {}).items():
            cmd += ["-D", f"{k}={v}"]
        cmd.append(str(ROOT / entry["file"]))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0 or not out.exists():
            raise RuntimeError(f"OpenSCAD failed: {proc.stderr[-600:]}")
        return trimesh.load(out)
