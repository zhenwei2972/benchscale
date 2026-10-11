"""The local viewer: the latest design, at real scale, next to what it holds.

Standard library only. It shows whatever was designed last - from the MCP
server, the CLI or the built-in chat - and refreshes when a new design lands.
"""

from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .. import design
from ..chat import credentials_available

INDEX = Path(__file__).with_name("index.html")
_sessions: dict[str, object] = {}
_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "benchscale/0.1"

    def log_message(self, fmt, *args):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, default=str).encode(), "application/json")

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self._send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
        if url.path == "/api/status":
            ok, why = credentials_available()
            return self._json(200, {"chat_available": ok, "detail": why})
        if url.path == "/api/scene":
            wanted = parse_qs(url.query).get("design", [None])[0]
            try:
                return self._json(200, design.load_scene(wanted))
            except FileNotFoundError:
                return self._json(404, {"error": "no designs yet"})
        if url.path == "/api/designs":
            root = design.designs_dir()
            items = sorted((p.name for p in root.iterdir() if (p / "scene.json").exists()), reverse=True)[:40]
            return self._json(200, {"designs": items})
        if url.path.startswith("/files/"):
            parts = url.path.split("/")
            if len(parts) == 4 and all(".." not in p for p in parts):
                path = design.designs_dir() / parts[2] / parts[3]
                if path.exists() and path.suffix in (".stl", ".json"):
                    return self._send(200, path.read_bytes(), "application/octet-stream")
            return self._json(404, {"error": "not found"})
        return self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/chat":
            return self._json(404, {"error": "not found"})
        ok, why = credentials_available()
        if not ok:
            return self._json(503, {"error": why})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
        text = (body.get("message") or "").strip()
        if not text:
            return self._json(400, {"error": "empty message"})
        sid = body.get("session") or uuid.uuid4().hex
        from ..chat import ChatSession
        with _lock:
            session = _sessions.setdefault(sid, ChatSession())
        try:
            result = session.send(text)
        except Exception as exc:  # surface API errors to the page, not a stack trace
            return self._json(502, {"error": f"{type(exc).__name__}: {exc}", "session": sid})
        return self._json(200, {**result, "session": sid})


def serve(port: int = 8742, host: str = "127.0.0.1") -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"benchscale viewer on http://localhost:{port}/  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
