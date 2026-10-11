import json
import threading
import urllib.error
import urllib.request

from benchscale import bases, tools


def test_tools_return_plain_json():
    out = tools.design_part("holder", {"object": "std:microscope_slide"})
    json.dumps(out)
    assert out["design_id"] and out["viewer"].startswith("http://localhost:")


def test_design_errors_come_back_as_messages_not_exceptions():
    out = tools.design_part("tip_box_dock", {"tilt_deg": 90})
    assert "error" in out and "maximum" in out["error"]


def test_base_models_are_listed_with_their_licence():
    catalog = bases.catalog()
    assert len(catalog) == 17
    rack = bases.find("conical_rack_50ml")
    assert rack["license"] == "CERN-OHL-P-2.0"
    assert {p["name"] for p in rack["params"]} >= {"rows", "cols", "pitch", "hole_d"}


def test_mcp_server_registers_every_tool():
    import asyncio
    from benchscale.mcp_server import create_server
    server = create_server()
    names = {t.name for t in asyncio.run(server.list_tools())}
    assert names == {f.__name__ for f in tools.TOOLS}


def test_viewer_serves_the_latest_design_and_refuses_chat_without_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr("benchscale.chat.Path.home", lambda: __import__("pathlib").Path("/nonexistent"))
    from http.server import ThreadingHTTPServer
    from benchscale.web.server import Handler
    out = tools.design_part("holder", {"object": "std:microscope_slide"})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    try:
        scene = json.load(urllib.request.urlopen(f"{base}/api/scene"))
        assert scene["id"] == out["design_id"]
        assert urllib.request.urlopen(f"{base}/files/{scene['id']}/print.stl").read()[:5]
        req = urllib.request.Request(f"{base}/api/chat", data=b'{"message": "hi"}', method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req)
            raise AssertionError("chat should need credentials")
        except urllib.error.HTTPError as exc:
            assert exc.code == 503 and "MCP" in json.load(exc)["error"]
    finally:
        httpd.shutdown()
