#!/usr/bin/env python3
"""Threaded static server for proto/.

Chrome fetches html+css+js together. python -m http.server is one thread
and answers empty when a connection stalls (ERR_EMPTY_RESPONSE).
"""

from __future__ import annotations

import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    proto = os.path.normpath(os.path.join(here, "..", "proto"))
    if args.root:
        root = args.root
    elif os.path.isfile(os.path.join(os.getcwd(), "index.html")):
        root = os.getcwd()
    else:
        root = proto
    os.chdir(root)
    httpd = ThreadingHTTPServer((args.bind, args.port), SimpleHTTPRequestHandler)
    print(f"Serving {os.getcwd()} on http://{args.bind}:{args.port}/", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
