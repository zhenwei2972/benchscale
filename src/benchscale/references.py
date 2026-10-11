"""Real objects, at real size: the reference library.

Every design in benchscale is built around things that exist - a tip rack, a
Falcon tube, a slide - and their sizes come from here, never from a guess.
Three sources, in order of authority:

1. measured  - what you measured on your own bench (calipers win);
2. standards - curated facts with a citation (data/standards.json);
3. opentrons - 164 labware definitions from the Opentrons library
               (Apache-2.0, data/opentrons/catalog.json).

Sizes are millimetres. A box reference has x (width), y (depth), z (height);
a cylinder has d (outside diameter) and h (height).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA = Path(__file__).parent / "data"


def state_dir() -> Path:
    """Where measured references and designs live (BENCHSCALE_HOME, default ~/.benchscale)."""
    path = Path(os.environ.get("BENCHSCALE_HOME", Path.home() / ".benchscale"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class Reference:
    id: str
    name: str
    kind: str
    shape: str                      # "box" or "cylinder"
    x: float | None = None
    y: float | None = None
    z: float | None = None
    d: float | None = None
    h: float | None = None
    features: dict = field(default_factory=dict)
    wells: list = field(default_factory=list)
    source: str = ""
    url: str = ""
    license: str = ""
    confidence: str = ""
    notes: str = ""

    @property
    def footprint(self) -> tuple[float, float]:
        if self.shape == "cylinder":
            return (self.d, self.d)
        return (self.x, self.y)

    @property
    def height(self) -> float:
        return self.h if self.shape == "cylinder" else self.z

    def size_text(self) -> str:
        if self.shape == "cylinder":
            return f"{self.d:g} mm O.D. x {self.h:g} mm"
        return f"{self.x:g} x {self.y:g} x {self.z:g} mm"

    def summary(self) -> dict:
        """What a person (or a model) needs to decide whether this is the right object."""
        return {"id": self.id, "name": self.name, "kind": self.kind, "shape": self.shape,
                "size": self.size_text(), "confidence": self.confidence, "source": self.source}

    def to_dict(self, wells: bool = False) -> dict:
        out = asdict(self)
        if not wells:
            out["wells"] = f"{len(self.wells)} wells (omitted)" if self.wells else []
        return {k: v for k, v in out.items() if v not in (None, "", {}, [])}


def _tokens(text: str) -> list[str]:
    text = text.lower().replace("µ", "u").replace("μ", "u")
    text = re.sub(r"(\d)\s*(ml|ul|mm)\b", r"\1\2", text)          # "1.5 mL" -> "1.5ml"
    return re.findall(r"[a-z0-9.]+", text)


class Library:
    def __init__(self, extra_path: Path | None = None) -> None:
        self.measured_path = extra_path or (state_dir() / "measured_references.json")
        self.refs: dict[str, Reference] = {}
        for entry in json.loads((DATA / "opentrons" / "catalog.json").read_text()):
            self._add(entry)
        for entry in json.loads((DATA / "standards.json").read_text()):
            self._add(entry)
        if self.measured_path.exists():
            for entry in json.loads(self.measured_path.read_text()):
                self._add(entry)

    def _add(self, entry: dict) -> Reference:
        ref = Reference(**{k: v for k, v in entry.items() if k in Reference.__dataclass_fields__})
        self.refs[ref.id] = ref
        return ref

    def get(self, ref_id: str) -> Reference:
        if ref_id in self.refs:
            return self.refs[ref_id]
        hits = self.search(ref_id, limit=1)
        if hits:
            return hits[0]
        raise KeyError(f"no reference matches {ref_id!r}; try search_references first")

    def search(self, query: str, kind: str | None = None, limit: int = 8) -> list[Reference]:
        """Rank by how many query words appear in the name, id, kind, brand and aliases.
        Measured references win ties: they are the user's own bench."""
        words = _tokens(query)
        scored = []
        for ref in self.refs.values():
            if kind and ref.kind != kind:
                continue
            hay = " ".join([ref.name, ref.id.replace("_", " "), ref.kind.replace("_", " "),
                            str(ref.features.get("brand") or ""),
                            " ".join(ref.features.get("aliases", []))])
            hay_tokens = set(_tokens(hay))
            hay_text = " ".join(hay_tokens)
            score = sum(2.0 if w in hay_tokens else (1.0 if w in hay_text else 0.0) for w in words)
            if score <= 0:
                continue
            score += {"measured": 0.6, "standard": 0.3}.get(ref.id.split(":")[0].replace("std", "standard"), 0.0)
            scored.append((score, -len(ref.name), ref))
        scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
        return [r for _, _, r in scored[:limit]]

    def add_measured(self, name: str, kind: str, shape: str, notes: str = "", **size: float) -> Reference:
        """Save something measured on the user's bench. It wins over library sizes."""
        if shape == "box" and not all(size.get(k) for k in ("x", "y", "z")):
            raise ValueError("a box needs x, y and z in mm")
        if shape == "cylinder" and not all(size.get(k) for k in ("d", "h")):
            raise ValueError("a cylinder needs d (outside diameter) and h in mm")
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:48]
        entry = {"id": f"measured:{slug}", "name": name, "kind": kind, "shape": shape,
                 **{k: float(v) for k, v in size.items() if v}, "source": "measured by the user",
                 "license": "user data", "confidence": "measured", "notes": notes}
        ref = self._add(entry)
        saved = json.loads(self.measured_path.read_text()) if self.measured_path.exists() else []
        saved = [e for e in saved if e["id"] != ref.id] + [entry]
        self.measured_path.write_text(json.dumps(saved, indent=1))
        return ref
