"""Third-party data, linked rather than bundled.

benchscale does not ship anyone else's files. data/thirdparty.json names what
it uses - Opentrons labware definitions (Apache-2.0) and the Prompt to Bench
OpenSCAD designs (CERN-OHL-P-2.0) - at pinned upstream commits. The first time
they are needed they are downloaded from GitHub into a local cache
(BENCHSCALE_CACHE, default ~/.cache/benchscale), under their own licences.
Set BENCHSCALE_OFFLINE=1 to never download; the reference library then holds
only the cited standards and your own measurements.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MANIFEST = json.loads((Path(__file__).parent / "data" / "thirdparty.json").read_text())
RAW_URL = "https://raw.githubusercontent.com/{repo}/{commit}/{path}"
UA = {"User-Agent": "benchscale (+https://github.com/zhenwei2972/benchscale)"}

KIND = {"tipRack": "tip_rack", "wellPlate": "plate", "tubeRack": "tube_rack", "reservoir": "reservoir",
        "aluminumBlock": "block", "adapter": "adapter", "lid": "lid", "trash": "trash", "other": "other",
        "system": "other"}


def cache_dir() -> Path:
    path = Path(os.environ.get("BENCHSCALE_CACHE", Path.home() / ".cache" / "benchscale"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def offline() -> bool:
    return os.environ.get("BENCHSCALE_OFFLINE", "") not in ("", "0", "false")


def _download(jobs: list[tuple[str, Path]], what: str) -> None:
    todo = [(u, p) for u, p in jobs if not p.exists()]
    if not todo:
        return
    print(f"benchscale: downloading {len(todo)} {what} from GitHub (once; cached in {cache_dir()})",
          file=sys.stderr)

    def get(job):
        url, path = job
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            data = r.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(path)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(get, todo))


# --- Opentrons labware -------------------------------------------------------------------------
def normalise_opentrons(d: dict, name: str) -> dict:
    meta, dims, params = d["metadata"], d["dimensions"], d.get("parameters", {})
    wells = []
    for wname in sorted(d.get("wells", {}), key=lambda n: (n[0], int(n[1:]) if n[1:].isdigit() else 0)):
        w = d["wells"][wname]
        well = {"name": wname, "x": w["x"], "y": w["y"], "z": w["z"], "depth": w["depth"], "shape": w["shape"]}
        if w["shape"] == "circular":
            well["diameter"] = w["diameter"]
        else:
            well["x_size"], well["y_size"] = w.get("xDimension"), w.get("yDimension")
        wells.append(well)
    brand = d.get("brand", {}) or {}
    first = d["wells"][wells[0]["name"]] if wells else {}
    return {
        "id": f"opentrons:{name}", "name": meta["displayName"],
        "kind": KIND.get(meta.get("displayCategory", "other"), "other"), "shape": "box",
        "x": dims["xDimension"], "y": dims["yDimension"], "z": dims["zDimension"],
        "features": {"brand": brand.get("brand"), "catalogue_numbers": brand.get("brandId", []),
                     "wells": len(wells), "tip_length": params.get("tipLength"),
                     "format": params.get("format"), "volume_ul": first.get("totalLiquidVolume")},
        "wells": wells,
        "source": "Opentrons labware library (downloaded from upstream, not bundled)",
        "url": f"https://github.com/Opentrons/opentrons/tree/{MANIFEST['opentrons']['commit']}"
               f"/shared-data/labware/definitions/2/{name}",
        "license": "Apache-2.0", "confidence": "manufacturer-derived definition",
        "notes": ("x and y are the base footprint as it sits on a robot deck; z is the full height, "
                  "including tips for a tip rack. A bench box with a lid or skirt can differ - "
                  "measure yours and add it as a measured reference if the fit matters."),
    }


def opentrons_catalog() -> list[dict]:
    """Opentrons labware as reference entries; [] when offline and not cached yet."""
    m = MANIFEST["opentrons"]
    root = cache_dir() / "opentrons" / m["commit"][:12]
    out = root / "catalog.json"
    if out.exists():
        return json.loads(out.read_text())
    if offline():
        return []
    jobs = [(RAW_URL.format(repo=m["repo"], commit=m["commit"], path=m["path"].format(name=n, version=v)),
             root / "raw" / f"{n}.json") for n, v in m["labware"]]
    try:
        _download(jobs, "Opentrons labware definitions (Apache-2.0)")
    except OSError as exc:
        print(f"benchscale: could not download Opentrons labware ({exc}); continuing without it",
              file=sys.stderr)
        return []
    entries = [normalise_opentrons(json.loads(p.read_text()), p.stem) for _, p in jobs]
    entries = [e for e in entries if e["x"] and e["y"] and e["z"]]   # skip sizeless software placeholders
    out.write_text(json.dumps(entries))
    return entries


# --- Prompt to Bench designs -------------------------------------------------------------------
def prompt_to_bench_root() -> Path | None:
    """Folder holding the Prompt to Bench .scad files; None when offline and not cached yet."""
    m = MANIFEST["prompt_to_bench"]
    root = cache_dir() / "prompt-to-bench" / m["commit"][:12]
    jobs = [(RAW_URL.format(repo=m["repo"], commit=m["commit"], path=f), root / f)
            for f in m["files"] + ["LICENSE"]]
    if all(p.exists() for _, p in jobs):
        return root
    if offline():
        return None
    try:
        _download(jobs, "Prompt to Bench designs (CERN-OHL-P-2.0)")
    except OSError as exc:
        print(f"benchscale: could not download Prompt to Bench ({exc})", file=sys.stderr)
        return None
    return root


def fetch_all() -> dict:
    return {"opentrons_labware": len(opentrons_catalog()),
            "prompt_to_bench_designs": len(MANIFEST["prompt_to_bench"]["files"]) if prompt_to_bench_root() else 0,
            "cache": str(cache_dir())}
