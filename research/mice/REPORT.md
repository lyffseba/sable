# SABLE mouse-as-light-gun: what to track (v1)

**Detect the whole mouse as an object; the gun point is the silhouette nose (front-taper contour extremum toward the camera / LMB–RMB split at the leading edge). Shot pixel = that nose, not the box center. Run YOLO11n (COCO, class 64 `mouse`) as a CPU proposal generator only — ONNX + OpenVINO INT8, imgsz=416, ~20–40 ms/frame on a 2021 G14 Ryzen 9 5900HS — then lock the nose with KLT (~1–2 ms) so the RTX 3060 stays on the game. Box center is the stock. Scroll wheel is heading, not the muzzle.**

This is arcade light-gun geometry (Duck Hunt / Time Crisis / House of the Dead): webcam on the **top of the monitor**, player points the **nose** at the glass. The bullet hits **exactly** that screen pixel. No aim-assist, no offset from box-center. Stills: 26 product/review photos, 16 scored below. YOLO11n COCO on CPU (this box, imgsz=640): median **25 ms**, **13/26** true `mouse` hits, **13 misses**, phone/airplane/vase/suitcase confusions. Neon tape remains optional ranked kit, not v1 average.

---

## Geometry (do not invert)

Monitor-top webcam looks at the player. Lifted mouse, nose toward camera. Camera sees: **front face**, some top/logo, maybe scroll wheel from 3/4. It does **not** see PTFE feet or the belly sensor unless the player aims the bottom at the glass (unnatural). Superlight front face is a USB recess; office mice put the **cable grommet** in the same place. That hole / leading-edge split **is** the muzzle.

```
  webcam
     v
  [ monitor ]
       ^  <-- nose / muzzle  =  shot pixel
     /  \     scroll wheel   =  top of barrel (heading only)
    |    |    hump / logo    =  stock
    \____/    box center     =  stock  (REJECT as primary)
     hand
```

---

## Corpus

26 stills in `images/` (fair-use research, not to ship). Cover: Superlight **white and black**, HP/Logitech M90–B100 office class, beige Logitech + IBM (no wheel), DeathAdder Elite/2013 front-oblique, G502 / G403 / G900, Razer Naga / Abyssus / Mamba, SteelSeries Rival RGB, lattice/honeycomb-class RGB (Pexels, not Model O). Prefer 3/4-front. Belly shot is a **negative**. Sources: `SOURCES.md`. Annotated YOLO: `annotated/`. Naive OpenCV silhouettes: `opencv/`. Contact sheet: `contact_sheet.jpg`. Raw numbers: `yolo_results.json`.

Wikimedia Superlight file 404; Logitech CDN galleries were 4 KB placeholders. Hippopx honeycomb 403. No Commons Glorious Model O.

---

## YOLO11n COCO (class 64 `mouse`) — empirical

Weights `yolo11n.pt`, conf≥0.15, imgsz=640, **CPU**. This machine median 25.1 ms / mean 30.1 / p90 42.6. G14 under game load will be slower (see model section).

| still | view | YOLO `mouse` | other / fail | notes for barrel |
|---|---|---|---|---|
| Superlight white B&H | 3/4 front | **0.23** | — | white-on-white, barely a mouse |
| Superlight black B&H | 3/4 front | **MISS** | **airplane 0.45** | box ate dongle; center = stock |
| Superlight black Unsplash | 3/4 on pad | **0.97** | potted plant 0.32 | best Superlight lock; pad contrast |
| DeathAdder Elite front | 3/4 front | 0.54 | — | best gun-pose analog |
| DeathAdder 2013 front | 3/4 front | 0.78 | — | cable = muzzle landmark |
| DeathAdder wheel close | macro | MISS | scissors 0.26 | wheel ≠ mouse |
| DeathAdder **belly** | underside | MISS | — | sensor **not** a gun-pose feature |
| HP M-U0031 office | top-down | MISS | — | office class, no lock |
| HP wired white-bg | 3/4 rear | 0.55 | — | nose points away |
| Logitech M100 | top-down desk | 0.57 | **cell phone 0.54** | famous confusion; 2nd box includes cable |
| Logitech B100 | top-down | **0.99** | — | easy top-down, still stock-center |
| Logitech beige optical | top | MISS | **vase 0.56** | beige office fails COCO |
| G502 3/4 | side | MISS | — | |
| G502 phone photo | high angle | MISS | — | |
| G403 RGB | top on stand | 0.89 | — | G logo = stock |
| G900 | clutter | MISS | — | |
| G7 3/4 | clutter | MISS | cell phone 0.20 | |
| Razer Naga 2014 | 3/4 | MISS | toaster (low) | RGB/logo not used |
| Razer Abyssus | top on pad | 0.59 | — | |
| Razer Mamba | clutter | MISS | suitcase 0.51 | |
| SteelSeries Rival RGB | 3/4 | 0.85 | — | wheel glow = heading |
| IBM PS/2 beige | 3/4 | MISS | phone/suitcase/scissors | **no scroll wheel** |
| Logitech blue optical | 3/4 | 0.77 | — | |
| Generic optical | clutter | MISS | train/truck | |
| Lancehead + DA | clutter | 0.66 | — | |
| Pexels lattice RGB | side | 0.66 | keyboard 0.49 | honeycomb-class proxy |

**13/26 mouse, 13 miss, 2 phone-only, 1 both.** COCO `mouse` is a **finder**, not a barrel. Box center on hits sits on the **hump**. White Superlight and beige office are the two v1 must-works — both are YOLO-fragile.

Naive global Otsu (no box) also fails: on the Unsplash Superlight the “nose” snapped to the **image corner** because the dark pad merged with the mouse. **Segment inside a proposal box**, then take the extremum.

---

## Scores as BARREL POINTS (0–5)

Not “easy to detect.” 5 = this point **is** the muzzle the bullet should leave. Averaged across the 16 representative stills (Superlight W/B, Unsplash Superlight, DA Elite, DA 2013, HP office, HP 3/4, M100, B100, beige Logitech, IBM beige, G502, G403, Rival RGB, Abyssus, lattice RGB). Per-photo notes follow.

| candidate | vis. from webcam-gun pose | unique vs hand/desk | stable across colors/brands | sub-pixel lock | on cheap office mouse | **as barrel** |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| whole-body box center | 4 | 3 | 2 | 1 | 4 | **0** |
| silhouette nose (front extremum) | **5** | 3 | **5** | **4** | **5** | **5** |
| scroll wheel (dark cylinder) | 4 | **4** | 3 | 4 | 4 | **1** |
| brand logo on hump | 1 | 3 | 1 | 2 | 1 | **0** |
| LMB/RMB split line | 4 | 3 | 4 | 3 | **5** | **3** |
| RGB strip | 2 | 4 | **0** | 3 | 0 | **0** |
| PTFE feet / belly sensor | **0** | 4 | 2 | 4 | 3 | **0** |

**Why the as-barrel column is not the mean of the other five.** Box center is easy to get and on every mouse — and it is the **stock**. A Time Crisis cabinet that shot from the stock would miss high. Logo and RGB live on the hump. Wheel sits **behind** the leading edge (top of the gun). IBM beige has **no wheel**. Superlight has **no RGB**. Belly sensor is invisible in gun pose (confirmed on DA 2013 underside). The only point that (a) exists on black Superlight **and** beige office, (b) faces the webcam, (c) is the muzzle, is the **front taper**.

LMB/RMB split is the **midline of that muzzle**, not a substitute point: use it to pick *which* contour pixel is the nose (the split at the leading edge), then fire from there.

### Per-photo barrel scores (nose / wheel / box / logo / split / RGB / belly)

| photo | nose | wheel | box | logo | split | RGB | belly |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Superlight white 3/4 | 5 | 4 | 1 | 0 | 5 | 0 | 0 |
| Superlight black 3/4 | 5 | 4 | 1 | 0 | 5 | 0 | 0 |
| Superlight Unsplash | 5 | 4 | 1 | 0 | 4 | 0 | 0 |
| DA Elite front | 5 | 4 | 1 | 1 | 4 | 0 | 0 |
| DA 2013 front | 5 | 4 | 1 | 1 | 4 | 0 | 0 |
| HP office optical | 5 | 3 | 1 | 1 | 5 | 0 | 0 |
| HP wired 3/4 | 4 | 3 | 1 | 2 | 4 | 0 | 0 |
| Logitech M100 | 5 | 4 | 1 | 0 | 4 | 0 | 0 |
| Logitech B100 | 5 | 4 | 1 | 0 | 4 | 0 | 0 |
| Beige Logitech optical | 5 | 4 | 1 | 1 | 5 | 0 | 0 |
| IBM PS/2 beige | 5 | **0** | 1 | 1 | 5 | 0 | 0 |
| G502 3/4 | 5 | 4 | 1 | 1 | 4 | 2 | 0 |
| G403 RGB | 5 | 3 | 1 | 0 | 4 | 1 | 0 |
| Rival 300 RGB | 5 | 4 | 1 | 0 | 4 | 3 | 0 |
| Abyssus / cheap RGB | 5 | 3 | 1 | 0 | 4 | 2 | 0 |
| Lattice honeycomb | 4 | 3 | 1 | 0 | 3 | 3 | 0 |

Honeycomb cutouts **hurt** silhouette purity (interior glow punches holes in the mask) but the front taper still exists. Wheel close-up and belly shot omitted from this table (not gun pose).

---

## Primary + fallback

**Primary (v1, no added hardware):** silhouette **nose** — contour extremum of the mouse mask **toward the camera**, snapped to the LMB/RMB split at the leading edge (or the cable/USB hole when visible). Present on black Superlight and beige office. Sub-pixel via contour/moments, not box center.

**Fallback (heading, not muzzle):** **scroll wheel** as second point. Two-point (nose + wheel) gives pitch/yaw; **the shot still leaves the nose**. Drop wheel on mice that lack one (IBM class) or when the wheel is occluded head-on.

**Do not** track: box center, G/Razer logo, RGB strip, PTFE, sensor.

**Pipeline**

1. Propose mouse: YOLO11n class 64 (or a 1-class nano trained on front-3/4 mice — better, later).
2. Mask inside the box (GrabCut / threshold + largest contour — **not** global Otsu).
3. Nose = extremum of that contour along the pointing axis (toward camera). Refine with the split line / cable hole.
4. Track the nose with KLT/optical flow at 30–60 fps.
5. Re-detect every N frames or on tracker failure / lift.
6. `AimSample.uv` = nose. HID click never waits on camera (existing SABLE rule).

---

## Model (30 fps, game keeps the GPU)

Target: 2021 G14, Ryzen 9 5900HS + RTX 3060 6GB. Game owns the 3060. Webcam 720p YUY2, AE off (TRACKING.md).

| option | 30 fps CPU? | notes |
|---|---|---|
| **YOLO11n ONNX + OpenVINO INT8, imgsz=416** | **yes, as proposal** | this box 25 ms @640 FP32 CPU; G14+game ~20–40 ms @416 INT8. **Pick this.** |
| YOLO11n @640 every frame | borderline | p90 43 ms here; G14 under load will drop under 30 fps |
| Custom 1-class nano (front mice) | yes, better recall | train later; COCO 50% is not a lock |
| YOLO-World / open-vocab | no | heavier, still a box |
| MobileSAM / SAM | no | GPU or too slow; optional refine on CPU is >frame |
| RF-DETR | no | too heavy for CPU 30 fps |
| MediaPipe Objectron | **EOL — do not** | |
| KLT / pyramidal Lucas–Kanade on the nose | **yes, <2 ms** | this is the 30 fps path once proposed |
| CSRT/KCF on whole mouse | maybe | tracks the **stock**; use only as a box prior |

**Latency guess (G14, game running, CPU only):** detect 25±10 ms every 3rd 720p frame (amortized ~8–12 ms) + KLT 1–2 ms → **comfortably 30 fps**, often 60 fps on the tracker. Do **not** bind TensorRT/CUDA. Export `yolo11n.pt` → ONNX → OpenVINO.

A later 1-class detector trained on *front-facing* mice (this corpus + phone captures of a Superlight and an M100 pointed at a laptop cam) will beat COCO on the exact failure cases (white Superlight, beige office, airplane). v1 ships COCO nano + nose KLT.

---

## Why neon tape still helps in ranked

v1 average: **no tape**. Black Superlight + beige office both have a front taper. Ranked / tournament:

1. **White Superlight on a white shirt** — COCO 0.23; silhouette dies. 6–8 mm **neon / IR tape on the vertical front face** (the USB recess plane) is a muzzle beacon, not a stock sticker.
2. **Hand wrap** — claw/palm covers the hump and sometimes the wheel; the front face usually stays visible. Tape on the nose survives grip.
3. **Head-on** — wheel foreshortens to a slit; tape on the front plane does not.
4. **Sub-pixel** — a high-contrast blob at the muzzle is a better KLT point than a matte black taper against a dark room.
5. **Two-dot heading** — nose tape + a second dot on the wheel or rear = cheap PnP without a sleeve.

**Optional ranked kit (not v1):** (1) neon/IR square on the **front face**, (2) second marker on the wheel well for heading, (3) last: a 3D-printed nose cap with an IR LED in the cable/USB hole. Sleeve/LED is kit, not the average-PC path.

---

## Failures to remember

- COCO `mouse` vs **cell phone** (M100 0.57 / 0.54).
- Superlight black product → **airplane 0.45** (dongle + 3/4 wedge).
- Beige office → **vase**.
- Wheel macro → **scissors**. Mamba → **suitcase**. Naga → toaster.
- Box that includes the **cable** shifts the center off the body (M100).
- Global Otsu on a dark pad **is not** a nose.
- Belly sensor is a high-quality feature that **the webcam will not see**.
- RGB is not on Superlight or office mice — cannot be v1.

---

## Verdict (one page)

Track the **mouse body**, fire from the **nose**. YOLO11n-CPU proposes; KLT holds the front-taper extremum at 30 fps without touching the 3060. Wheel is the backup heading point. Tape on the muzzle for ranked. Do not ship box-center aim.
