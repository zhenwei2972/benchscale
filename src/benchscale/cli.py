"""benchscale command line."""

from __future__ import annotations

import argparse
import json
import sys


def _params(pairs: list[str]) -> dict:
    out = {}
    for pair in pairs or []:
        key, _, value = pair.partition("=")
        if not _:
            raise SystemExit(f"parameter {pair!r} should look like name=value")
        out[key.strip()] = value.strip()
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="benchscale", description="Lab apparatus, designed at real scale.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("refs", help="search the reference library"); s.add_argument("query", nargs="+")
    s.add_argument("--kind")
    s = sub.add_parser("ref", help="show one reference"); s.add_argument("ref_id")
    s = sub.add_parser("measure", help="save an object you measured (mm)")
    s.add_argument("name"); s.add_argument("--kind", default="other")
    s.add_argument("--box", nargs=3, type=float, metavar=("X", "Y", "Z"))
    s.add_argument("--cylinder", nargs=2, type=float, metavar=("D", "H"))
    sub.add_parser("templates", help="list templates")
    s = sub.add_parser("template", help="describe a template's parameters"); s.add_argument("name")
    s = sub.add_parser("design", help="build a part from a template")
    s.add_argument("template"); s.add_argument("-p", "--param", action="append", default=[], help="name=value")
    s.add_argument("--printer", default="bambu_a1_mini")
    s = sub.add_parser("bases", help="list free base models"); s.add_argument("query", nargs="*")
    s = sub.add_parser("serve", help="run the viewer (and chat) on localhost")
    s.add_argument("--port", type=int, default=8742)
    sub.add_parser("mcp", help="run the MCP server over stdio (for Claude Desktop / Claude Code)")
    s = sub.add_parser("chat", help="one chat message from the terminal (needs Anthropic credentials)")
    s.add_argument("message", nargs="+")
    args = ap.parse_args(argv)

    from . import tools
    if args.cmd == "refs":
        out = tools.search_references(" ".join(args.query), args.kind)
        for r in out["results"]:
            print(f"{r['id']:<58} {r['size']:<32} {r['confidence']}")
        return
    if args.cmd == "ref":
        print(json.dumps(tools.get_reference(args.ref_id), indent=1)); return
    if args.cmd == "measure":
        if bool(args.box) == bool(args.cylinder):
            raise SystemExit("give exactly one of --box X Y Z or --cylinder D H")
        if args.box:
            x, y, z = args.box
            out = tools.add_measured_reference(args.name, args.kind, "box", x=x, y=y, z=z)
        else:
            d, h = args.cylinder
            out = tools.add_measured_reference(args.name, args.kind, "cylinder", d=d, h=h)
        print(json.dumps(out, indent=1)); return
    if args.cmd == "templates":
        for t in tools.list_templates()["templates"]:
            print(f"{t['name']:<14} {t['summary']}")
        return
    if args.cmd == "template":
        print(json.dumps(tools.describe_template(args.name), indent=1)); return
    if args.cmd == "design":
        out = tools.design_part(args.template, _params(args.param), args.printer)
        if "error" in out:
            raise SystemExit(f"error: {out['error']}")
        print(f"design {out['design_id']}: {' x '.join(f'{v:.1f}' for v in out['size_mm'])} mm")
        for c in out["checks"]:
            mark = {True: "ok  ", False: "FAIL", None: "    "}[c["ok"]]
            print(f"  [{mark}] {c['name']}: {c['value']}  ({c['basis']})")
        for n in out["notes"]:
            print(f"  - {n}")
        print(f"STL (print orientation): {out['files']['print_stl']}")
        print(f"viewer: {out['viewer']}")
        sys.exit(1 if out["failed_checks"] else 0)
    if args.cmd == "bases":
        out = tools.list_base_models(" ".join(args.query))
        for b in out["base_models"]:
            print(f"{b['id']:<44} {b['name']}")
        if not out["openscad_installed"]:
            print("(OpenSCAD is not installed: listing works, rendering needs it)")
        return
    if args.cmd == "serve":
        from .web.server import serve
        serve(args.port); return
    if args.cmd == "mcp":
        from .mcp_server import main as mcp_main
        mcp_main(); return
    if args.cmd == "chat":
        from .chat import ChatSession, credentials_available
        ok, why = credentials_available()
        if not ok:
            raise SystemExit(why)
        out = ChatSession().send(" ".join(args.message))
        print(out["reply"])
        for d in out["designs"]:
            print(f"design: {d}")


if __name__ == "__main__":  # pragma: no cover
    main()
