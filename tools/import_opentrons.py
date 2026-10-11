"""Turn the Opentrons labware definitions into benchscale's reference catalogue.

The raw definitions (Apache-2.0) are kept unmodified in data/opentrons/raw/.
This writes data/opentrons/catalog.json: one entry per labware with its
outer size, its wells (position, shape, size, depth) and where it came from.

Refresh the raw files first with `benchscale import-opentrons --fetch`.
"""

from __future__ import annotations

import json
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "src/benchscale/data/opentrons/raw"
OUT = RAW.parent / "catalog.json"
URL = "https://github.com/Opentrons/opentrons/blob/edge/shared-data/labware/definitions/2/{name}"

KIND = {"tipRack": "tip_rack", "wellPlate": "plate", "tubeRack": "tube_rack", "reservoir": "reservoir",
        "aluminumBlock": "block", "adapter": "adapter", "lid": "lid", "trash": "trash", "other": "other",
        "system": "other"}


def normalise(path: Path) -> dict:
    d = json.loads(path.read_text())
    meta, dims, params = d["metadata"], d["dimensions"], d.get("parameters", {})
    wells = []
    for name in sorted(d.get("wells", {}), key=lambda n: (n[0], int(n[1:]) if n[1:].isdigit() else 0)):
        w = d["wells"][name]
        well = {"name": name, "x": w["x"], "y": w["y"], "z": w["z"], "depth": w["depth"], "shape": w["shape"]}
        if w["shape"] == "circular":
            well["diameter"] = w["diameter"]
        else:
            well["x_size"], well["y_size"] = w.get("xDimension"), w.get("yDimension")
        wells.append(well)
    brand = d.get("brand", {}) or {}
    return {
        "id": f"opentrons:{path.stem}",
        "name": meta["displayName"],
        "kind": KIND.get(meta.get("displayCategory", "other"), "other"),
        "shape": "box",
        "x": dims["xDimension"], "y": dims["yDimension"], "z": dims["zDimension"],
        "features": {
            "brand": brand.get("brand"), "catalogue_numbers": brand.get("brandId", []),
            "wells": len(wells), "tip_length": params.get("tipLength"),
            "format": params.get("format"), "volume_ul": (wells[0].get("depth") and
                                                           d["wells"][wells[0]["name"]].get("totalLiquidVolume")) if wells else None,
        },
        "wells": wells,
        "source": "Opentrons labware library",
        "url": URL.format(name=path.stem),
        "license": "Apache-2.0",
        "confidence": "manufacturer-derived definition",
        "notes": ("x and y are the base footprint as it sits on a robot deck; z is the full height, "
                  "including tips for a tip rack. A bench box with a lid or skirt can differ - "
                  "measure yours and add it as a measured reference if the fit matters."),
    }


def main() -> None:
    entries = [normalise(p) for p in sorted(RAW.glob("*.json"))]
    # Software placeholders (e.g. protocol_engine_lid_stack_object) have no size: not bench objects.
    skipped = [e["id"] for e in entries if not (e["x"] and e["y"] and e["z"])]
    entries = [e for e in entries if e["x"] and e["y"] and e["z"]]
    OUT.write_text(json.dumps(entries, indent=1))
    print(f"wrote {len(entries)} entries to {OUT}; skipped {len(skipped)} without a size: {skipped}")


if __name__ == "__main__":
    main()
