import pytest

from benchscale import design
from benchscale.references import Library
from benchscale.templates import registry


@pytest.mark.parametrize("template, params", [
    ("tip_box_dock", {}),
    ("tip_box_dock", {"box": "opentrons:eppendorf_96_tiprack_1000ul_eptips", "tilt_deg": 0, "finger_notches": False}),
    ("tube_rack", {}),
    ("tube_rack", {"tube": "std:eppendorf_1p5ml", "rows": 4, "cols": 6}),
    ("holder", {"object": "std:microscope_slide"}),
    ("holder", {"object": "std:falcon_15ml"}),
])
def test_every_template_builds_a_closed_part_that_clears_what_it_holds(template, params, tmp_path):
    out = design.run(template, params, out_root=tmp_path)
    by_name = {c["name"]: c for c in out["checks"]}
    assert by_name["one closed solid"]["ok"]
    assert by_name["reference objects fit without touching the walls"]["ok"]
    assert (tmp_path / out["design_id"] / "print.stl").exists()


def test_the_pocket_is_the_reference_plus_clearance():
    lib = Library()
    t = registry()["tip_box_dock"]
    d = t.build(t.resolve({"tilt_deg": 0, "clearance": 0.5}, lib), lib)
    ref = lib.get("opentrons:tipone_96_tiprack_200ul")
    # flat dock: outer size = rack + 2 x clearance + 2 x wall, to the hundredth
    assert d.part.bounding_box.extents[0] == pytest.approx(ref.x + 2 * 0.5 + 2 * 3.0, abs=0.01)


def test_parameters_are_checked_against_their_limits():
    t = registry()["tip_box_dock"]
    with pytest.raises(ValueError, match="above the maximum"):
        t.resolve({"tilt_deg": 45}, Library())
    with pytest.raises(ValueError, match="unknown parameter"):
        t.resolve({"tilt": 10}, Library())


def test_a_part_too_big_for_the_printer_fails_its_check(tmp_path):
    out = design.run("tube_rack", {"tube": "std:falcon_50ml", "rows": 4, "cols": 5}, out_root=tmp_path)
    fit = next(c for c in out["checks"] if c["name"].startswith("fits the"))
    assert fit["ok"] is False
