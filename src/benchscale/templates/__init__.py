"""Parametric part templates. Each one is built around reference objects.

A template declares its parameters (with units, defaults and limits) so a chat
model can ask for exactly what it needs, and returns a Design: the part, the
reference objects placed where they will sit (ghosts), and checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import trimesh

from ..references import Library, Reference


@dataclass
class Param:
    name: str
    kind: str                   # "float", "int", "bool", "reference"
    default: object
    description: str
    unit: str = ""
    min: float | None = None
    max: float | None = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and v != ""}


@dataclass
class Placed:
    """A reference object where it sits in (or on) the design, for the viewer and the checks."""
    name: str
    ref_id: str
    mesh: trimesh.Trimesh


@dataclass
class Check:
    name: str
    ok: bool | None             # None = informational
    value: str
    detail: str = ""
    basis: str = "computed from the model"

    def __post_init__(self) -> None:
        if self.ok is not None:
            self.ok = bool(self.ok)          # numpy booleans do not serialise

    def to_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class Design:
    template: str
    params: dict
    part: trimesh.Trimesh                       # in the orientation it is used
    print_part: trimesh.Trimesh | None = None   # in the orientation it prints, if different
    ghosts: list[Placed] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)


class Template:
    name: str = ""
    title: str = ""
    summary: str = ""
    params: list[Param] = []

    def resolve(self, given: dict, lib: Library) -> dict:
        """Defaults, type conversion and limits - complain clearly rather than build nonsense."""
        known = {p.name: p for p in self.params}
        unknown = sorted(set(given) - set(known))
        if unknown:
            raise ValueError(f"unknown parameter(s) {unknown}; {self.name} takes {sorted(known)}")
        out = {}
        for p in self.params:
            value = given.get(p.name, p.default)
            if p.kind == "float":
                value = float(value)
            elif p.kind == "int":
                value = int(round(float(value)))
            elif p.kind == "bool":
                value = value if isinstance(value, bool) else str(value).lower() in ("1", "true", "yes", "on")
            elif p.kind == "reference":
                value = lib.get(str(value)).id
            if p.kind in ("float", "int"):
                if p.min is not None and value < p.min:
                    raise ValueError(f"{p.name} = {value} is below the minimum {p.min} {p.unit}".rstrip())
                if p.max is not None and value > p.max:
                    raise ValueError(f"{p.name} = {value} is above the maximum {p.max} {p.unit}".rstrip())
            out[p.name] = value
        return out

    def describe(self) -> dict:
        return {"name": self.name, "title": self.title, "summary": self.summary,
                "params": [p.to_dict() for p in self.params]}

    def build(self, params: dict, lib: Library) -> Design:  # pragma: no cover - abstract
        raise NotImplementedError


def registry() -> dict[str, Template]:
    from .holder import Holder
    from .tip_box_dock import TipBoxDock
    from .tube_rack import TubeRack
    return {t.name: t for t in (TipBoxDock(), TubeRack(), Holder())}
