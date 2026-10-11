"""benchscale as an MCP server: any Claude client becomes the design chat.

Add it to Claude Desktop or Claude Code (see README), then describe what you
need in plain words. Claude finds the real objects, picks a template, builds
the part and reports the checks; the viewer at http://localhost:8742 shows it.
"""

from __future__ import annotations

import asyncio
import logging

from mcp.server.mcpserver import MCPServer

from . import tools

INSTRUCTIONS = """\
Design 3D-printable lab apparatus at real scale.

Sizes always come from the reference library or the user's own measurements -
never estimate a dimension yourself. The library holds 164 Opentrons labware
definitions (tip racks, plates, tube racks, reservoirs), cited standards
(SBS/ANSI microplate footprint, Falcon 15/50 mL, 1.5 mL tubes, test tubes,
slides) and anything the user has measured.

1. Identify every object the part must hold or fit: search_references, then
   get_reference for detail and the source of the numbers.
2. If the user has the object in hand, offer to use their caliper reading
   (add_measured_reference). Measured sizes win over library sizes.
3. Pick a template (list_templates, describe_template) and call design_part.
4. Report plainly: size, each check that passed or failed (keep its
   "computed" or "ESTIMATED" label), the viewer link and the STL path.
5. If no template fits, say so; offer the closest template or a free base
   model (list_base_models).
"""


def create_server() -> MCPServer:
    server = MCPServer(name="benchscale", title="benchscale - lab apparatus at real scale",
                       version="0.1.0", instructions=INSTRUCTIONS)

    @server.tool()
    async def search_references(query: str, kind: str | None = None, limit: int = 8) -> dict:
        """Find real objects by name: 'falcon 50 ml', 'eppendorf 1000 tip rack', '96 well plate'.
        kind narrows it: tip_rack, plate, tube, tube_rack, reservoir, slide, block, adapter."""
        return tools.search_references(query, kind, limit)

    @server.tool()
    async def get_reference(ref_id: str, include_wells: bool = False) -> dict:
        """Full detail for one reference: size, features, source of the numbers, licence."""
        return tools.get_reference(ref_id, include_wells)

    @server.tool()
    async def add_measured_reference(name: str, kind: str, shape: str, x: float = 0, y: float = 0,
                                     z: float = 0, d: float = 0, h: float = 0, notes: str = "") -> dict:
        """Save an object the user measured (mm). shape 'box': x width, y depth, z height;
        'cylinder': d outside diameter, h height. Measured sizes are used ahead of library sizes."""
        return tools.add_measured_reference(name, kind, shape, x, y, z, d, h, notes)

    @server.tool()
    async def list_templates() -> dict:
        """The part templates, each built around reference objects."""
        return tools.list_templates()

    @server.tool()
    async def describe_template(name: str) -> dict:
        """A template's parameters with units, defaults and limits."""
        return tools.describe_template(name)

    @server.tool()
    async def design_part(template: str, params: dict | None = None, printer: str = "bambu_a1_mini") -> dict:
        """Build a part from a template around real reference objects and check it.
        Returns checks (labelled computed or ESTIMATED), size, STL files and a viewer link."""
        return await asyncio.to_thread(tools.design_part, template, params or {}, printer)

    @server.tool()
    async def list_base_models(query: str = "") -> dict:
        """Free, openly licensed starting designs (Prompt to Bench, CERN-OHL-P-2.0)."""
        return tools.list_base_models(query)

    @server.tool()
    async def render_base_model(base_id: str, params: dict | None = None, printer: str = "bambu_a1_mini") -> dict:
        """Render a base model with chosen parameters (needs OpenSCAD) and check it."""
        return await asyncio.to_thread(tools.render_base_model, base_id, params or {}, printer)

    @server.tool()
    async def printers() -> dict:
        """Printers whose build volume the checks know."""
        return tools.printers()

    return server


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    create_server().run("stdio")


if __name__ == "__main__":  # pragma: no cover
    main()
