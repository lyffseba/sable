#!/usr/bin/env python3
"""Threaded static server for proto/ plus SABLE JSON APIs."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

here = os.path.dirname(os.path.abspath(__file__))
if here not in sys.path:
    sys.path.insert(0, here)

try:
    from gemini_muzzle_tracker import detect_mouse_in_image
except ImportError:
    detect_mouse_in_image = None

try:
    import sable_mojo
except ImportError:
    sable_mojo = None

try:
    import lobby as lobby_api
except ImportError:
    lobby_api = None


class SableRequestHandler(SimpleHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self) -> None:
        raw = self.path.split("?", 1)
        path = raw[0]
        qs = raw[1] if len(raw) > 1 else ""
        if path == "/api/health":
            mojo_id = sable_mojo.ping() if sable_mojo else None
            self._json(
                {
                    "ok": True,
                    "game": "sable",
                    "mojo": mojo_id,
                    "gemini": bool(detect_mouse_in_image),
                    "lobby": bool(lobby_api),
                }
            )
            return
        if path == "/api/lobby" and lobby_api:
            code = ""
            for part in qs.split("&"):
                if part.startswith("code="):
                    code = part.split("=", 1)[1]
            self._json(lobby_api.get(code))
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path == "/api/lobby/create" and lobby_api:
                d = self._read_json()
                self._json(lobby_api.create(str(d.get("name") or "HOST")))
                return
            if path == "/api/lobby/join" and lobby_api:
                d = self._read_json()
                self._json(lobby_api.join(str(d.get("code") or ""), str(d.get("name") or "PLAYER")))
                return
            if path == "/api/lobby/leave" and lobby_api:
                d = self._read_json()
                self._json(lobby_api.leave(str(d.get("code") or ""), str(d.get("player") or "")))
                return
            if path == "/api/lobby/start" and lobby_api:
                d = self._read_json()
                self._json(lobby_api.start(str(d.get("code") or ""), str(d.get("player") or "")))
                return

            if path == "/api/gemini/lock":
                data = self._read_json()
                img_b64 = data.get("image", "")
                if "," in img_b64:
                    img_b64 = img_b64.split(",", 1)[1]
                img_bytes = base64.b64decode(img_b64)
                if detect_mouse_in_image:
                    res = detect_mouse_in_image(img_bytes)
                else:
                    res = {"detected": False, "error": "Gemini tracker not loaded"}
                self._json(res)
                return

            if path == "/api/mojo/centroid":
                if not sable_mojo:
                    self._json({"ok": False, "error": "mojo unavailable"}, 503)
                    return
                d = self._read_json()
                self._json(
                    sable_mojo.centroid(
                        int(d["width"]),
                        int(d["height"]),
                        int(d["blob_x"]),
                        int(d["blob_y"]),
                        int(d["radius"]),
                    )
                )
                return

            if path == "/api/mojo/hitscan":
                if not sable_mojo:
                    self._json({"ok": False, "error": "mojo unavailable"}, 503)
                    return
                d = self._read_json()
                self._json(
                    sable_mojo.hitscan(
                        list(d["origin"]),
                        list(d["direction"]),
                        list(d["sphere"]),
                        float(d["radius"]),
                    )
                )
                return
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, 400)
            return

        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    proto = os.path.normpath(os.path.join(here, "..", "proto"))
    if args.root:
        root = args.root
    elif os.path.isfile(os.path.join(os.getcwd(), "index.html")):
        root = os.getcwd()
    else:
        root = proto
    os.chdir(root)
    mojo_id = sable_mojo.ping() if sable_mojo else None
    httpd = ThreadingHTTPServer((args.bind, args.port), SableRequestHandler)
    print(
        f"Serving {os.getcwd()} on http://{args.bind}:{args.port}/ "
        f"(gemini={bool(detect_mouse_in_image)} mojo={mojo_id or 'off'})",
        flush=True,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
