# benchscale

**Describe a piece of lab apparatus in plain words; get a printable part sized against the real objects it
holds.**

Small custom bench parts cost a lab real money. A tilted dock for a tip box, a rack for an odd tube, or a
loader for bulk tips gets sold as a "custom" catalogue item, or someone spends an afternoon in CAD. A
3D printer makes them for cents, but only if the part fits first time. benchscale makes real scale the core
of the design:

- **A reference library of real objects.** It links to 163 labware definitions from Opentrons (tip racks,
  plates, reservoirs, tube racks; downloaded on first use), cited standards (the 96-well footprint, Falcon tubes, test tubes, slides,
  pipette tips), and anything you measure yourself. Every size carries its source and a confidence label.
- **Parametric templates built around those objects.** The object is placed in the design as a "ghost"
  and checked for collisions, so a pocket that is too small fails a check instead of a print.
- **Checks you can trust.** Each one is labelled *computed from the model* or *ESTIMATED*, and the two are
  never mixed.
- **Three ways in:** Claude Desktop or Claude Code (first party, no API key), GitHub Codespaces in the
  browser with your own key, or the command line. A local 3D viewer shows every design.

## 3D Print for Science

**Scientists and students in Singapore: describe a bench part you need, and we design it for free.**

[**Submit a request**](https://github.com/zhenwei2972/benchscale/issues/new?template=print-request.yml) ·
[open queue](https://github.com/zhenwei2972/benchscale/issues?q=is%3Aissue+is%3Aopen+label%3Aprint-request) ·
[**design gallery**](https://zhenwei2972.github.io/benchscale/) (spin the models, download the STLs)

- **The designs are AI-generated.** Claude builds them with benchscale, and they are research and
  development quality. The more detail you give, the better the part.
- **Printing is best effort.** There is one Bambu Lab A1 mini, printing PLA up to about 175 mm a side, in
  queue order. No turnaround is promised.
- **Designs are free and open.** Every design is published here for anyone to print.
- **Not for:** sterile or autoclaved use, use on people, or anything hazardous.

**Good requests name the real objects, give sizes, and say what goes wrong today.** For example:

> Dock for an Axygen T-200-Y 200 µL tip box (standard 128 x 86 mm footprint), tilted 15° towards me, so it
> stops sliding in the biosafety cabinet. The top of the box must stay under 120 mm.

> Rack for 8 Falcon 50 mL tubes in two rows that fits our 90 mm-wide fridge shelf. The tubes must stand,
> not lean.

> Holder for a 25 x 75 mm microscope slide at 30° for photographing under a phone camera, with a
> 10 mm ledge so the slide cannot slip.

The form is public, so do not include personal details or anything confidential.

## Get started

**Test prints so far.** The 12-hole shake-fill coupon set (deck, stand and lid) printed successfully on a
Bambu Lab A1 mini in PLA on 11 Oct 2026. It took 68 min against a 72 min slicer estimate, and the camera
frames at each stage show all three parts intact, with no stringing or detached parts. Filling it with real
tips has not been measured yet, and the full 96-hole rack and the tip-box dock have not been printed.

There are three ways to use benchscale. Claude Desktop and Claude Code use your Claude account, so you
need no API key.

| Way | Best for | You need |
|---|---|---|
| [Claude Desktop](#1-claude-desktop) | Chatting your way to a part | Claude Desktop, Python 3.10+ |
| [Claude Code](#2-claude-code) | Working in a terminal, or changing templates | Claude Code, Python 3.10+ |
| [GitHub Codespaces](#3-github-codespaces-nothing-to-install) | Trying it with nothing installed | A GitHub account |

### Install (for Claude Desktop, Claude Code or the command line)

benchscale needs **Python 3.10 or newer**. The `python3` that ships with macOS is 3.9 and will not
work. These steps use [uv](https://docs.astral.sh/uv/), which installs the right Python for you:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh          # once; or: brew install uv
git clone https://github.com/zhenwei2972/benchscale && cd benchscale
uv venv --python 3.12 && uv pip install -e ".[dev]"
.venv/bin/benchscale fetch                                # downloads the linked labware data, about 10 s
.venv/bin/benchscale templates                            # should list four templates
```

### 1. Claude Desktop

1. Do the install above, then print the full path of the `benchscale` command:
   `echo "$PWD/.venv/bin/benchscale"`
2. In Claude Desktop open **Settings → Developer → Edit Config**. Add this to `claude_desktop_config.json`,
   using your path, and save:
   ```json
   {"mcpServers": {"benchscale": {"command": "/full/path/to/benchscale/.venv/bin/benchscale", "args": ["mcp"]}}}
   ```
3. Quit and reopen Claude Desktop. "benchscale" should appear among the connectors.
4. Check it works: ask *"List the benchscale templates."* Then ask for a part, for example *"Our bulk
   Axygen 200 µL tips take ages to rack. Make me something that loads them."*
5. To see each design in 3D, run `.venv/bin/benchscale serve` and open http://localhost:8742. It refreshes
   on every new design.

### 2. Claude Code

1. Do the install above, then start Claude Code inside the folder with the environment active:
   ```bash
   source .venv/bin/activate && claude
   ```
2. The repository's `.mcp.json` registers the benchscale server. Approve it when Claude Code asks. If it
   doesn't ask, add it yourself: `claude mcp add benchscale -- "$PWD/.venv/bin/benchscale" mcp`
3. Check it works: ask *"List the benchscale templates."* Steps 4 and 5 of Claude Desktop apply here too.

### 3. GitHub Codespaces (nothing to install)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/zhenwei2972/benchscale?quickstart=1)

The button opens benchscale in your own cloud workspace on GitHub, ready to use. The first start takes a
few minutes while it installs; later starts are quicker. Claude Code and the 3D viewer are both set up.

1. Click the button, then **Create codespace**.
2. When it opens, the viewer starts on port 8742. Open it from the **Ports** tab if it does not appear.
3. Choose how to chat:
   - **Claude Code, no API key.** Type `claude` in the terminal and sign in with your Claude account. The
     benchscale tools are already connected.
   - **Built-in chat in the viewer, with your own API key.** Add a Codespaces secret named
     `ANTHROPIC_API_KEY` at [github.com/settings/codespaces](https://github.com/settings/codespaces)
     (**New secret**, choose this repository), then restart the codespace. GitHub may also offer it as a
     recommended secret when you create the codespace.

How your key is kept safe:
- **It stays in your GitHub account.** GitHub stores Codespaces secrets encrypted and passes them only to
  your own codespaces, as an environment variable.
- **We never see it.** benchscale has no server of its own, and the key goes only from your codespace to
  Anthropic.
- **Usage is billed to your Anthropic account**, at standard API rates.
- **The codespace is yours.** Stop or delete it when you are done. GitHub's free monthly allowance for
  personal accounts covers light use.

### Command line only

```bash
.venv/bin/benchscale refs falcon 50                       # search the reference library
.venv/bin/benchscale template shake_fill_rack             # parameters, units and limits
.venv/bin/benchscale design shake_fill_rack -p rows=3 -p cols=4 -p hole_step=0.3
.venv/bin/benchscale serve                                # http://localhost:8742
```

### Troubleshooting

- **"requires a different Python" or "editable mode requires setuptools"**: your Python is too old. Use the
  uv steps above.
- **Claude can't start benchscale**: use the full path to `.venv/bin/benchscale` in the config. Claude
  Desktop does not see your shell's PATH.
- **No network**: set `BENCHSCALE_OFFLINE=1`. The library then holds only the cited standards and your
  own measurements.
- **`benchscale bases` can't render**: rendering the Prompt to Bench base models needs
  [OpenSCAD](https://openscad.org). Listing them does not.

## Templates

| Template | What it makes |
|---|---|
| `shake_fill_rack` | A 96-position tip rack that loads itself from loose bulk tips (below) |
| `tip_box_dock` | Holds a tip box tilted toward you, gripped so it cannot slide, with finger notches and recesses for rubber feet |
| `tube_rack` | A rack for any tube in the library or one you measured; prints upside down without support |
| `holder` | A block with a pocket shaped to one object: a plate, slide, bottle or tube |

`benchscale template <name>` lists each template's parameters with units and limits.

## Featured: a tip rack that fills itself from bulk tips

Bulk tips cost about half as much as racked ones. Racking them by hand is slow, and the printable
loaders people share need a hand-fixing pass afterwards. Two failures cause that: a tip goes in upside
down, or a tip drops into a filled position and stacks inside the tip already there.

`shake_fill_rack` is designed so neither can happen:

![Cut through one row of the deck](docs/shake_fill_section.svg)

- **Each hole is narrower than the tip's collar.** A tip can only enter point first and then hangs by
  its collar. Collar first, it stops on the ledge and topples off when shaken.
- **A filled position stands 3.5 mm proud of the funnel peaks.** That makes a full hole a bump and an
  empty hole a dip. Loose tips slide off the full holes and into the empty ones, instead of being funnelled
  into a seated tip's open top.
- **The funnels overlap like an egg crate.** The model has 0.0% flat land on the deck top (computed), so a
  tip has nowhere to lie still.
- **It is three parts, each printed flat without support:** the deck, a stand that holds it at the height
  the tips hang, and a lid you hold on while shaking.

**How-to video:** [docs/shake_fill_howto.mp4](docs/shake_fill_howto.mp4) (53 s, a keyframed true-scale animation of the parts, rebuilt with `tools/export_video_assets.py` and `blender -b -P tools/howto_video.py`).

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
[NOTICE](NOTICE).

## Licence

MIT for benchscale's own code. Linked third-party data keeps its own licence (see NOTICE).
