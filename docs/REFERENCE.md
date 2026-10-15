# Reference

Templates, the demo request, free base models, and where every number comes from.

## Templates

| Template | What it makes |
|---|---|
| `shake_fill_rack` | A 96-position tip rack that loads itself from loose bulk tips (below) |
| `tip_box_dock` | Holds a tip box tilted toward you, gripped so it cannot slide, with finger notches and recesses for rubber feet |
| `tube_rack` | A rack for any tube in the library or one you measured; prints upside down without support |
| `holder` | A block with a pocket shaped to one object: a plate, slide, bottle or tube |

`benchscale template <name>` lists each template's parameters with units and limits.

## Demo: a tilted dock for a tip box

The request: *"We keep a TipOne 200 µL rack at the back of the biosafety cabinet and lean over it all
day; it slides when I load the 8-channel. Make me a dock that tilts it toward me about 15 degrees, grips it
so it can't slide, lets me lift it out with two fingers, and keeps the top of the box under 120 mm so it
clears the sash."*

`python examples/demo_mcp_client.py` makes the same tool calls Claude makes over MCP: search_references,
get_reference, describe_template and design_part. The result:

- **Size:** 134.8 × 97.7 × 38.9 mm, one closed solid, fits the A1 mini (computed).
- **Fit:** the rack sits in a 128.76 × 86.48 mm pocket, built from the TipOne definition's 127.76 × 85.48 mm
  base. The rack does not touch the walls (overlap 0.000 mm³, computed).
- **Slicer estimate (ESTIMATED):** 2 h 31 min and 72.9 g of PLA. Whether the box stays put at the 15°
  tilt is also ESTIMATED.

## Free base models

`benchscale bases` lists 17 OpenSCAD designs from
[Prompt to Bench](https://github.com/ATinyGreenCell/prompt-to-bench) (CERN-OHL-P-2.0). They are not
bundled: they are downloaded from that repository the first time you list them. Rendering them needs
[OpenSCAD](https://openscad.org) on the PATH.

## Where the numbers come from

| Source | Licence | Confidence |
|---|---|---|
| Your measurements (`benchscale measure`) | yours | measured; these win over everything else |
| `data/standards.json`, cited per entry | facts | standard / manufacturer nominal / ESTIMATED |
| [Opentrons labware library](https://github.com/Opentrons/opentrons/tree/edge/shared-data/labware), 163 definitions | Apache-2.0 | manufacturer-derived definitions |

No third-party files are bundled. The Opentrons definitions and Prompt to Bench designs are downloaded
from their own repositories at pinned commits the first time they are needed (about 10 seconds), into
`~/.cache/benchscale`. `benchscale fetch` does it up front, and `BENCHSCALE_OFFLINE=1` turns it off. See
[NOTICE](../NOTICE).

