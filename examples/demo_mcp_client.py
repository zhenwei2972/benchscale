"""Drive benchscale over MCP exactly as a Claude client does, and print each step.

This is the demo in docs/DEMO.md: the request comes from a scientist in plain
words; the tool calls below are the ones the chat model makes to answer it.
Run:  python examples/demo_mcp_client.py
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REQUEST = ("We keep a TipOne 200 uL rack at the back of the biosafety cabinet and lean over it all day; "
           "it slides when I load the 8-channel. Make me a dock that tilts it toward me about 15 degrees, "
           "grips it so it can't slide, lets me lift it out with two fingers, and keeps the top of the "
           "box under 120 mm so it clears the sash.")

STEPS = [
    ("search_references", {"query": "TipOne 200 tip rack", "kind": "tip_rack", "limit": 3}),
    ("get_reference", {"ref_id": "opentrons:tipone_96_tiprack_200ul"}),
    ("describe_template", {"name": "tip_box_dock"}),
    ("design_part", {"template": "tip_box_dock", "params": {
        "box": "opentrons:tipone_96_tiprack_200ul", "tilt_deg": 15, "finger_notches": True,
        "feet": True, "max_height": 120}}),
]


async def main() -> None:
    exe = shutil.which("benchscale") or sys.executable.replace("python", "benchscale")
    params = StdioServerParameters(command=exe, args=["mcp"])
    print(f"REQUEST: {REQUEST}\n")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            tools = await session.list_tools()
            print(f"connected to {init.server_info.name}: {len(tools.tools)} tools\n")
            for name, args in STEPS:
                result = await session.call_tool(name, args)
                body = json.loads(result.content[0].text)
                print(f"-> {name}({json.dumps(args)})")
                print(json.dumps(body, indent=1)[:2500], "\n")


if __name__ == "__main__":
    asyncio.run(main())
