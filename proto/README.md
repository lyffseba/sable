# LIFTSHOT

Physical-aim shooter. On the mat the mouse is a mouse. Lift it, point it at the screen like a gun, click to fire.

You never see your face. The webcam stays hidden; nothing from the camera is drawn on the game canvas. After PLAY the front webcam locks a **48×48 patch of stock mouse plastic** (no tape) the way a Superlight sensor locks the mat. That patch’s motion is the aim.

## Hardware

- Lightweight wireless mouse (Logitech Superlight class). Stock only.
- Webcam at the **top of the monitor**. **Tilt it down at your hands, not your face.** Sit ~40cm+ back.
- Chrome on localhost (camera needs a secure origin; `file://` fails).

## Run

```
cd liftshot
python3 -m http.server 8080
```

Open **http://localhost:8080**. PLAY. Allow camera if prompted.

## Play

1. PLAY
2. Hold the mouse up to the webcam. We lock the plastic like the sensor locks the mat. Tilt the cam at your hands. Stay on SEEKING until a template exists — the game does **not** fall back to the OS mouse.
3. Four corners light up — aim the mouse-gun, click each, then one center shot.
4. 60-second arcade wave. Lift, point, click.

## Keys

| Key | What |
|-----|------|
| **T** | Hidden debug: desktop-aim (OS mouse moves the crosshair) |
| **Space** (hold) | Force GUN mode |

Mode chip: `PAD` / `GUN` / `DESKTOP` / `SEEKING`.

## Aim

The webcam watches a compact patch of the mouse body (top 30% of the camera is cropped so the face is out of the working image). Normalized cross-correlation tracks that patch each frame; 2D position maps through a 4-corner homography. Recalibrate if you move the webcam or change seats.
