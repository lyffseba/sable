#!/usr/bin/env python3
"""Threaded static server for proto/.

Chrome fetches html+css+js together. python -m http.server is one thread
and answers empty when a connection stalls (ERR_EMPTY_RESPONSE).
"""

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


class SableRequestHandler(SimpleHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path == "/api/gemini/lock":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                img_b64 = data.get("image", "")
                if "," in img_b64:
                    img_b64 = img_b64.split(",", 1)[1]
                img_bytes = base64.b64decode(img_b64)
                if detect_mouse_in_image:
                    res = detect_mouse_in_image(img_bytes)
                else:
                    res = {"detected": False, "error": "Gemini tracker not loaded"}
            except Exception as e:
                res = {"detected": False, "error": str(e)}

            resp_bytes = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
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
    httpd = ThreadingHTTPServer((args.bind, args.port), SableRequestHandler)
    print(f"Serving {os.getcwd()} on http://{args.bind}:{args.port}/ (Gemini 3.8 Flash Muzzle API enabled)", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
