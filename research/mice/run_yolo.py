#!/usr/bin/env python3
"""YOLO COCO + OpenCV inventory for SABLE mouse-as-light-gun study."""
from __future__ import annotations
import json, time
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path("/workspace/sable/research/mice")
IMG_DIR = ROOT / "images"
ANN_DIR = ROOT / "annotated"
OCV_DIR = ROOT / "opencv"
ANN_DIR.mkdir(exist_ok=True)
OCV_DIR.mkdir(exist_ok=True)

# COCO names of interest
TRACK = {"mouse", "cell phone", "remote", "keyboard", "laptop", "tv", "clock",
         "sports ball", "bottle", "cup", "book", "scissors", "toothbrush",
         "hair drier", "teddy bear"}

def load_model():
    for w in ("yolo11n.pt", "yolov8n.pt"):
        try:
            m = YOLO(w)
            print("loaded", w)
            return m, w
        except Exception as e:
            print("fail", w, e)
    raise SystemExit("no yolo weights")

def ocv_inventory(bgr, name):
    """Cheap visual inventory: silhouette + darkest blob (wheel proxy) + front extremum."""
    h, w = bgr.shape[:2]
    # downscale for speed
    scale = 640 / max(h, w)
    if scale < 1:
        small = cv2.resize(bgr, (int(w*scale), int(h*scale)))
    else:
        small = bgr.copy()
        scale = 1.0
    sh, sw = small.shape[:2]
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Otsu fg/bg — works on studio white; weaker on clutter
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # keep largest contour
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    vis = small.copy()
    nose = None
    area = 0
    if cnts:
        c = max(cnts, key=cv2.contourArea)
        area = float(cv2.contourArea(c))
        cv2.drawContours(vis, [c], -1, (0, 255, 0), 2)
        # "toward camera" in product 3/4 is often the rightmost or bottom-most
        # We mark BOTH extrema: min-y (top of frame, often rear in top-down)
        # and the point farthest from contour centroid along the major axis.
        M = cv2.moments(c)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            cv2.circle(vis, (int(cx), int(cy)), 6, (255, 0, 0), -1)  # STOCK / box-center analog
            pts = c.reshape(-1, 2).astype(np.float32)
            d = pts - np.array([cx, cy], np.float32)
            # PCA-ish: farthest from centroid
            i = int(np.argmax((d**2).sum(1)))
            nose = (int(pts[i, 0]), int(pts[i, 1]))
            cv2.circle(vis, nose, 8, (0, 0, 255), -1)  # NOSE candidate (red)
            cv2.putText(vis, "NOSE?", (nose[0]+8, nose[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
            cv2.putText(vis, "CENT", (int(cx)+8, int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)
    # dark-cylinder proxy: very dark compact blobs
    dark = (gray < 40).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    dc, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wheel_n = 0
    for dcnt in dc:
        a = cv2.contourArea(dcnt)
        if 30 < a < 0.02 * sh * sw:
            x,y,bw,bh = cv2.boundingRect(dcnt)
            ar = bw / max(bh, 1)
            if 0.4 < ar < 2.5:
                cv2.rectangle(vis, (x,y), (x+bw,y+bh), (0,255,255), 1)
                wheel_n += 1
    out = OCV_DIR / f"ocv_{name}"
    cv2.imwrite(str(out), vis)
    return {
        "contour_area_frac": round(area / (sh*sw + 1e-6), 4),
        "nose_xy_downscaled": nose,
        "dark_blob_candidates": wheel_n,
        "ocv_path": str(out),
    }

def main():
    model, weights = load_model()
    files = sorted([p for p in IMG_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}])
    rows = []
    # warmup
    dummy = np.zeros((640, 640, 3), np.uint8)
    _ = model.predict(dummy, device="cpu", imgsz=640, verbose=False)
    times = []
    for p in files:
        bgr = cv2.imread(str(p))
        if bgr is None:
            rows.append({"file": p.name, "error": "unreadable"})
            continue
        h, w = bgr.shape[:2]
        t0 = time.perf_counter()
        res = model.predict(bgr, device="cpu", imgsz=640, conf=0.15, verbose=False)[0]
        dt = (time.perf_counter() - t0) * 1000
        times.append(dt)
        names = res.names
        dets = []
        mouse_hits = []
        phone_hits = []
        for box in res.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = [float(x) for x in box.xyxy[0].tolist()]
            bw = xyxy[2] - xyxy[0]
            bh = xyxy[3] - xyxy[1]
            area_frac = (bw * bh) / (w * h)
            label = names.get(cls, str(cls))
            rec = {"cls": cls, "name": label, "conf": round(conf, 3),
                   "xyxy": [round(v,1) for v in xyxy],
                   "box_wh": [round(bw,1), round(bh,1)],
                   "area_frac": round(area_frac, 4)}
            dets.append(rec)
            if label == "mouse":
                mouse_hits.append(rec)
            if label == "cell phone":
                phone_hits.append(rec)
        # annotated
        plotted = res.plot()
        cv2.imwrite(str(ANN_DIR / p.name), plotted)
        ocv = ocv_inventory(bgr, p.name)
        rows.append({
            "file": p.name,
            "wh": [w, h],
            "infer_ms_cpu": round(dt, 1),
            "n_dets": len(dets),
            "mouse": mouse_hits,
            "cell_phone": phone_hits,
            "all": [d for d in dets if d["name"] in TRACK or d["conf"] >= 0.25],
            "opencv": ocv,
        })
        mconf = mouse_hits[0]["conf"] if mouse_hits else None
        pconf = phone_hits[0]["conf"] if phone_hits else None
        others = [d["name"] for d in dets if d["name"] not in ("mouse",)]
        print(f"{p.name:48} {w}x{h}  {dt:6.0f}ms  mouse={mconf} phone={pconf} other={others[:6]}")

    # contact sheet of originals (max 16)
    thumbs = []
    for p in files[:16]:
        im = cv2.imread(str(p))
        if im is None:
            continue
        im = cv2.resize(im, (320, 240))
        cv2.putText(im, p.name[:28], (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,255,0), 1)
        thumbs.append(im)
    if thumbs:
        cols = 4
        rows_n = (len(thumbs) + cols - 1) // cols
        while len(thumbs) < rows_n * cols:
            thumbs.append(np.zeros((240, 320, 3), np.uint8))
        grid = np.vstack([np.hstack(thumbs[i*cols:(i+1)*cols]) for i in range(rows_n)])
        cv2.imwrite(str(ROOT / "contact_sheet.jpg"), grid)

    summary = {
        "weights": weights,
        "n_images": len(files),
        "cpu_infer_ms_mean": round(float(np.mean(times)), 1) if times else None,
        "cpu_infer_ms_median": round(float(np.median(times)), 1) if times else None,
        "cpu_infer_ms_p90": round(float(np.percentile(times, 90)), 1) if times else None,
        "mouse_detected": sum(1 for r in rows if r.get("mouse")),
        "phone_confused": sum(1 for r in rows if r.get("cell_phone") and not r.get("mouse")),
        "both_mouse_and_phone": sum(1 for r in rows if r.get("mouse") and r.get("cell_phone")),
        "miss": sum(1 for r in rows if not r.get("mouse")),
        "rows": rows,
    }
    outj = ROOT / "yolo_results.json"
    outj.write_text(json.dumps(summary, indent=2))
    print("\n=== SUMMARY ===")
    print(json.dumps({k: summary[k] for k in summary if k != "rows"}, indent=2))
    print("wrote", outj)

if __name__ == "__main__":
    main()
