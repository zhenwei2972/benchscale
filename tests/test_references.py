import pytest

from benchscale.references import Library


def test_library_loads_standards_and_all_opentrons_definitions():
    lib = Library()
    assert sum(1 for r in lib.refs.values() if r.id.startswith("opentrons:")) == 163   # 164 minus one sizeless placeholder
    sbs = lib.get("std:sbs_footprint")
    assert (sbs.x, sbs.y) == (127.76, 85.48)           # ANSI SLAS 1-2004


def test_every_reference_says_where_its_numbers_come_from():
    for ref in Library().refs.values():
        assert ref.source and ref.license and ref.confidence, ref.id
        assert (ref.x and ref.y and ref.z) if ref.shape == "box" else (ref.d and ref.h), ref.id


@pytest.mark.parametrize("query, expected", [
    ("falcon 50 ml", "std:falcon_50ml"),
    ("1.5 mL eppendorf tube", "std:eppendorf_1p5ml"),
    ("tipone 200 tip rack", "opentrons:tipone_96_tiprack_200ul"),
    ("eppendorf 1000 tip rack", "opentrons:eppendorf_96_tiprack_1000ul_eptips"),
])
def test_search_finds_the_obvious_object(query, expected):
    assert Library().search(query)[0].id == expected


def test_measured_sizes_persist_and_win_ties(isolated_home):
    lib = Library()
    lib.add_measured("Our TipOne 200 box", "tip_rack", "box", x=128.2, y=86.0, z=96.5)
    again = Library()                                          # a fresh process sees it too
    ref = again.get("measured:our_tipone_200_box")
    assert (ref.x, ref.y, ref.z) == (128.2, 86.0, 96.5) and ref.confidence == "measured"
    assert again.search("tipone 200 box")[0].id == ref.id


def test_measured_reference_must_be_complete():
    with pytest.raises(ValueError, match="cylinder needs"):
        Library().add_measured("bottle", "bottle", "cylinder", d=50.0)
