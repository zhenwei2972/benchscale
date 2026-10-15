# The shake-fill tip rack

Bulk tips cost about half as much as racked ones. Racking them by hand is slow, and the printable
loaders people share need a hand-fixing pass afterwards. Two failures cause that: a tip goes in upside
down, or a tip drops into a filled position and stacks inside the tip already there.

`shake_fill_rack` is designed so neither can happen:

![Cut through one row of the deck](shake_fill_section.svg)

- **Each hole is narrower than the tip's collar.** A tip can only enter point first and then hangs by
  its collar. Collar first, it stops on the ledge and topples off when shaken.
- **A filled position stands 3.5 mm proud of the funnel peaks.** That makes a full hole a bump and an
  empty hole a dip. Loose tips slide off the full holes and into the empty ones, instead of being funnelled
  into a seated tip's open top.
- **The funnels overlap like an egg crate.** The model has 0.0% flat land on the deck top (computed), so a
  tip has nowhere to lie still.
- **It is three parts, each printed flat without support:** the deck, a stand that holds it at the height
  the tips hang, and a lid you hold on while shaking.

**How-to video:** [docs/shake_fill_howto.mp4](shake_fill_howto.mp4) (53 s, a keyframed true-scale animation of the parts, rebuilt with `tools/export_video_assets.py` and `blender -b -P tools/howto_video.py`).

To load it, pour on about 1.5 times as many tips as there are holes and put the lid on. Shake side to side
for 10 to 20 seconds, then lift the lid. Tilt the rack, without turning it over, to pour the extra tips back.

**Fit your tips before printing the full rack.** Corning publishes no dimensioned drawing of the Axygen
T-200-Y, so the tip sizes in the library are ESTIMATED (collar 7.0 mm, body 5.6 mm, 51 mm long). The coupon
settles it with your own tips on your own printer:

```bash
benchscale design shake_fill_rack -p piece=deck -p rows=3 -p cols=4 -p hole_step=0.3
```

This makes a 12-hole deck with hole sizes of 5.65, 5.95, 6.25 and 6.55 mm, one size per column. Column 1
is next to the cut corner. The right column holds a tip upright with its collar down in the pocket. Then
build the full rack with that size, using `-p hole=<mm>`, or pass your caliper readings with
`-p collar_od=` and `-p body_od=`.

These are the slicer's figures (ESTIMATED; Bambu Studio, A1 mini, 0.2 mm layers, 15% infill):

| Print | Time | PLA |
|---|---|---|
| Coupon deck, 12 holes | 19 min | 3.4 g |
| Coupon set, deck + stand + lid | 1 h 12 min | 32.9 g |
| Full rack: deck | 1 h 21 min | 19.9 g |
| Full rack: stand | 1 h 24 min | 48.7 g |
| Full rack: lid | 1 h 05 min | 43.0 g |

The price difference comes from Corning eCatalog list prices (Middle East region, 11 Oct 2026). Bulk
T-200-Y costs $668.13 per 20,000 tips, about $0.033 each. Racked T-200-Y-R costs $324.75 per 4,800, about
$0.068 each. Racking bulk tips saves about $3.30 per 96 tips. The full rack uses 112 g of PLA (slicer
ESTIMATE), about $2 at $20 per kg.

**Test print:** the 12-hole coupon set (deck, stand and lid) printed successfully on 11 Oct 2026, taking 68 min
on the A1 mini. How well it fills with real tips (holes filled, and in how many seconds) is the next
measurement, and is not reported yet.

Note that PLA is not autoclavable; it softens near 60 °C. Use the rack for non-sterile tips such as T-200-Y.

**Prior art, credited and not copied:**
- [ETH Zurich iGEM 2016 tip stacker](https://2016.igem.org/Team:ETH_Zurich/Hardware): shake tips into a
  printed rack, then transfer them with a comb.
- [Vapecream's modular tip sorting box](https://www.printables.com/model/896781-modular-pippette-tip-sorting-box),
  and its parametric remix [11mbs/pipette-tip-sorter](https://github.com/11mbs/pipette-tip-sorter). The
  remix's notes about tips squeezing into the same slot and holes left empty shaped the failure analysis
  above.

