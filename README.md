# benchscale

**Describe a lab part in plain words and get a 3D-printable design that fits the real thing.**

Labs pay catalogue prices for small "custom" bench parts: a tilted dock for a tip box, a rack for an odd
tube, a loader for bulk pipette tips. A desktop 3D printer can make them for a few cents of plastic, but
only if the part fits first time. benchscale designs every part around the real objects it holds, such as
a tip box, a Falcon tube or a slide, using their published sizes. It then checks the fit before anything is
printed.

**Try it now, with nothing to install:**
- [**Design gallery**](https://zhenwei2972.github.io/benchscale/): spin the 3D models and download the
  print files.
- [**Walkthrough: a tip sorter from request to print**](docs/examples/tip-sorter-walkthrough.md): the
  prompt, design screenshots, safety checks and the print report.
- [**How-to video**](docs/shake_fill_howto.mp4): loading bulk pipette tips with the shake-fill rack (53 s).
- [**Request a part**](https://github.com/zhenwei2972/benchscale/issues/new?template=print-request.yml), if
  you are a scientist or student in Singapore (see below).

**Printed so far:** the 12-hole test version of the shake-fill tip rack printed successfully on a
Bambu Lab A1 mini on 11 Oct 2026, in 68 minutes. How well it fills with real tips has not been measured
yet.

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

## Use it yourself

| Way | Good for | You need |
|---|---|---|
| **Claude Desktop** | Chatting your way to a part | Claude Desktop and Python 3.10+ |
| **Claude Code** | Working in a terminal, or changing the designs | Claude Code and Python 3.10+ |
| **GitHub Codespaces** | Trying it in a browser with nothing installed | A GitHub account (and your own API key for the built-in chat) |

Step-by-step setup for each, plus troubleshooting: **[docs/SETUP.md](docs/SETUP.md)**. Claude Desktop and
Claude Code use your Claude account, so you need no API key.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/zhenwei2972/benchscale?quickstart=1)

Once it's connected, just ask, for example *"Make me a rack for six 50 mL Falcon tubes"*. Claude finds the
real tube sizes, builds the part, and shows you every check. Each check is labelled either measured on the
3D model or an estimate. To print it, pair benchscale with
**[the Bambu Lab printer tools](https://github.com/zhenwei2972/Model-hardware-standard-Bambu-labs-)**.
They prepare the file with Bambu Studio, check it, print it and report on how it went.

## What it can make

- **[A tip rack that fills itself](docs/SHAKE_FILL_RACK.md).** Pour on bulk tips, shake, and they drop in
  point first. It can't load a tip upside down, and tips don't stack inside each other.
- **A tilted dock for a tip box**, so it can't slide in the biosafety cabinet.
- **Racks for any tube**, from 1.5 mL to Falcon 50 mL, or one you measure yourself.
- **Holders shaped to one object**, such as a plate, slide or bottle.

All templates, the demo request, the free starting models and the sources of every number:
[docs/REFERENCE.md](docs/REFERENCE.md).

## Where the sizes come from

benchscale keeps no one else's files. It links to
[Opentrons' labware library](https://github.com/Opentrons/opentrons/tree/edge/shared-data/labware)
(Apache-2.0) and [Prompt to Bench](https://github.com/ATinyGreenCell/prompt-to-bench)
(CERN-OHL-P-2.0), and downloads them the first time they're needed. Other sizes come from cited
standards and manufacturer data, and your own caliper measurements always win. See [NOTICE](NOTICE).

## Licence

MIT for benchscale's own code. Linked third-party data keeps its own licence.
