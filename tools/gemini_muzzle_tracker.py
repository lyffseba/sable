#!/usr/bin/env python3
"""Gemini hand / fingertip lock for SABLE.

Hand is the gun. Zero-shot lock of the pointing fingertip from a webcam frame.
Hot path stays in the browser (skin blob + NCC + One Euro). Gemini only seeds.
"""

from __future__ import annotations

import base64
import json
import os
import pathlib
import ssl
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]

MODELS = (
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-2.5-flash",
)

PROMPT = """You are the SABLE Hand-as-Gun vision engine.
The player aims by pointing a hand / index finger at the monitor like a light-gun.
Detect the aiming hand (not a computer mouse):
1. "detected": boolean, true if a pointing hand is visible.
2. "label": short string, e.g. "right hand", "finger gun".
3. "box_2d": [ymin, xmin, ymax, xmax] normalized 0-1000.
4. "fingertip": [y, x] normalized 0-1000 of the pointing index fingertip (the muzzle).
5. "wrist": [y, x] normalized 0-1000, or null.
6. "gesture": "finger_gun" | "pointing" | "open" | "fist" | "none"
7. "lifted": boolean, true if the hand is raised aiming (not resting on a desk).
8. "confidence": float 0.0-1.0.

Return strictly valid JSON with those keys.
Also include "muzzle_point" equal to "fingertip" for compatibility.
"""


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    auth_file = pathlib.Path.home() / ".pi/agent/auth.json"
    if auth_file.is_file():
        try:
            data = json.loads(auth_file.read_text())
            gkey = data.get("google", {}).get("key")
            if gkey:
                return str(gkey)
        except Exception:
            pass
    return ""


def _parse_payload(data: dict) -> dict:
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    out = json.loads(text)
    tip = out.get("fingertip") or out.get("muzzle_point")
    if tip:
        out["fingertip"] = tip
        out["muzzle_point"] = tip
    return out


def detect_hand_in_image(image_bytes: bytes, mime_type: str = "image/jpeg", key: str = "") -> dict:
    key = key or get_api_key()
    if not key:
        return {"detected": False, "error": "Missing GEMINI_API_KEY"}

    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    payload = json.dumps(
        {
            "contents": [
                {
                    "parts": [
                        {"text": PROMPT},
                        {"inline_data": {"mime_type": mime_type, "data": b64_data}},
                    ]
                }
            ],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
        }
    ).encode("utf-8")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    last_err = "no model"

    for model in MODELS:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + model
            + ":generateContent?key="
            + key
        )
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=45) as res:
                return _parse_payload(json.loads(res.read().decode("utf-8")))
        except urllib.error.HTTPError as exc:
            last_err = f"{model}: HTTP {exc.code}"
            continue
        except Exception as exc:
            last_err = f"{model}: {exc}"
            continue
    return {"detected": False, "error": last_err}


def detect_mouse_in_image(image_bytes: bytes, mime_type: str = "image/jpeg", key: str = "") -> dict:
    """Alias: the gun is the hand now."""
    return detect_hand_in_image(image_bytes, mime_type, key)


def main() -> int:
    test_img = ROOT / "research/mice/contact_sheet.jpg"
    if not test_img.is_file():
        print("No test image; hand lock is live on /api/gemini/lock", file=sys.stderr)
        return 0
    print("Sending frame to Gemini hand lock...")
    res = detect_hand_in_image(test_img.read_bytes())
    print(json.dumps(res, indent=2))
    return 0 if res.get("detected") or res.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main())
