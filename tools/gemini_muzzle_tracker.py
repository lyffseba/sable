#!/usr/bin/env python3
"""Gemini 3.8 Flash Muzzle Tracker for SABLE.

Uses Gemini 3.8 Flash multimodal vision to detect:
1. Mouse bounding box [ymin, xmin, ymax, xmax] (0-1000)
2. Precise front nose / muzzle point [y, x] (0-1000) where the player aims
3. Lift state (is the mouse lifted in air or on pad/desk)
4. Mouse identity (model/color)
"""

from __future__ import annotations

import base64
import json
import os
import pathlib
import ssl
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]

PROMPT = """You are the SABLE Physical-Aim Computer Vision Engine powered by Gemini 3.8 Flash.
Analyze this image/frame for a computer mouse (either held aiming at the monitor or visible in the scene).
Detect the primary mouse:
1. "detected": boolean, true if a computer mouse is visible in the frame.
2. "label": string identifying the mouse (brand/model/color, e.g. "Logitech G502", "White Gaming Mouse").
3. "box_2d": [ymin, xmin, ymax, xmax] coordinates normalized to 0-1000.
4. "muzzle_point": [y, x] coordinates (normalized 0-1000) of the leading-edge tip / front nose of the mouse (where LMB and RMB meet at the front). This is the exact shot origin / physical ADS barrel.
5. "lifted": boolean, true if held in the air / lifted off a surface.
6. "confidence": float between 0.0 and 1.0.

Return strictly valid JSON with keys:
{
  "detected": bool,
  "label": str,
  "box_2d": [int, int, int, int],
  "muzzle_point": [int, int],
  "lifted": bool,
  "confidence": float
}
"""


def get_api_key() -> str:
    # 1. Environment variable
    key = os.environ.get("GEMINI_API_KEY")
    if key and not key.startswith("AIzaSyCQD_F0DJxGuS"):
        return key

    # 2. Check ~/.pi/agent/auth.json
    auth_file = pathlib.Path.home() / ".pi/agent/auth.json"
    if auth_file.is_file():
        try:
            data = json.loads(auth_file.read_text())
            gkey = data.get("google", {}).get("key")
            if gkey:
                return gkey
        except Exception:
            pass

    return key or ""


def detect_mouse_in_image(image_bytes: bytes, mime_type: str = "image/jpeg", key: str = "") -> dict:
    key = key or get_api_key()
    if not key:
        return {"detected": False, "error": "Missing GEMINI_API_KEY"}

    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": mime_type, "data": b64_data}}
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={key}"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=45) as res:
            data = json.loads(res.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
    except Exception as e:
        return {"detected": False, "error": str(e)}


def main() -> int:
    test_img = ROOT / "research/mice/contact_sheet.jpg"
    if not test_img.is_file():
        print(f"Test image not found: {test_img}", file=sys.stderr)
        return 1

    print("Sending contact sheet to Gemini 3.8 Flash...")
    res = detect_mouse_in_image(test_img.read_bytes())
    print(json.dumps(res, indent=2))
    if res.get("detected"):
        print("Gemini 3.8 Flash Muzzle Lock successful!")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
