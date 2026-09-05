/* SABLE — hands.js
   MediaPipe Hands / skin+NCC tracker. detectForVideo lives in hands_worker.js.
   One Euro on UV, then the aim mailbox. Fire never waits on camera or the worker. */

import { S, W, H, phase, fire, clamp } from "./aim.js";
import { cam, proc, pctx, camReady } from "./boot.js";

const PROC_W = 480;
const CROP_TOP = 0.30;
const LOCK_SAMPLE_MS = 1200;
const LOCK_CONFIRM_MS = 200;
const LOCK_GIVE_MS = 4000;
const TPL_FAIL_MS = 2200;
const COAST_MS = 100;
const OUTLIER_FRAC = 0.18;
const QUALITY_LOST_MS = 280;
const TPL = 48;
const NCC_GOOD = 0.58;
const SEARCH_R = 56;
const FIND_STEP = 8;
const EURO_MINCUTOFF = 3.0, EURO_BETA = 0.03, EURO_DCUTOFF = 1.0;

export let PROC_H = 270;

function euroAlpha(dt, cutoff) { const r = 2 * Math.PI * cutoff * dt; return r / (r + 1); }
function makeEuro() { return { x: 0, dx: 0, t: 0, ready: false }; }
function euroStep(f, t, value, mincutoff, beta, dcutoff) {
  if (!f.ready) { f.x = value; f.dx = 0; f.t = t; f.ready = true; return value; }
  const dt = Math.max(1e-4, (t - f.t) * 0.001);
  const aD = euroAlpha(dt, dcutoff);
  const dx = (value - f.x) / dt;
  const dxHat = aD * dx + (1 - aD) * f.dx;
  const a = euroAlpha(dt, mincutoff + beta * Math.abs(dxHat));
  f.x = a * value + (1 - a) * f.x;
  f.dx = dxHat; f.t = t;
  return f.x;
}

function resetTrackFilters() {
  S.euroX = makeEuro(); S.euroY = makeEuro(); S.vel.x = 0; S.vel.y = 0;
}

function coastTrack(now) {
  if (!S.smooth) return;
  const age = now - S.lastDetAt;
  const dt = Math.max(0, (now - (S.trackT || now)) * 0.001);
  if (dt > 0 && age <= COAST_MS) {
    S.smooth.x = clamp(S.smooth.x + S.vel.x * dt, 0, PROC_W - 1);
    S.smooth.y = clamp(S.smooth.y + S.vel.y * dt, 0, PROC_H - 1);
  }
  S.trackT = now;
}

function updateQuality(now, hand) {
  const recency = clamp(1 - (now - (S.lastDetAt || 0)) / QUALITY_LOST_MS, 0, 1);
  const conf = hand && hand.conf != null ? hand.conf : recency * 0.2;
  const raw = (conf * 0.65 + recency * 0.35) * 100;
  S.quality += (raw - S.quality) * (hand ? 0.45 : 0.22);
}
// --- Computer Vision & Template Matching ---
function predictedCam(now) {
  if (!S.smooth) return null;
  const dt = Math.max(0, (now - (S.trackT || now)) * 0.001);
  return { x: S.smooth.x + S.vel.x * dt, y: S.smooth.y + S.vel.y * dt };
}

function isSkinByte(r, g, b) {
  const max = r > g ? (r > b ? r : b) : (g > b ? g : b);
  const min = r < g ? (r < b ? r : b) : (g < b ? g : b);
  const diff = max - min;
  if (max < 45 || max > 252 || diff < 16) return 0;
  if (r + 8 < g || r + 4 < b) return 0;
  const s = (diff * 255) / max;
  if (s < 28 || s > 220) return 0;
  let h = 0;
  if (max === r) h = ((g - b) * 60 / diff + 360) % 360;
  else if (max === g) h = (b - r) * 60 / diff + 120;
  else h = (r - g) * 60 / diff + 240;
  return (h <= 52 || h >= 335) ? 1 : 0;
}

function isSkinHSV(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const diff = max - min;
  let h = 0;
  if (diff > 1e-6) {
    if (max === r) h = (g - b) / diff + (g < b ? 6 : 0);
    else if (max === g) h = (b - r) / diff + 2;
    else h = (r - g) / diff + 4;
    h *= 60;
  }
  const s = max === 0 ? 0 : diff / max;
  const v = max;
  return ((h <= 50) || (h >= 340)) && s >= 0.15 && s <= 0.78 && v >= 0.22 && v <= 0.98;
}

function extractPatch(gray, w, tlx, tly) {
  const p = new Float32Array(TPL * TPL);
  for (let j = 0; j < TPL; j++) {
    const src = (tly + j) * w + tlx;
    const dst = j * TPL;
    for (let i = 0; i < TPL; i++) p[dst + i] = gray[src + i];
  }
  return p;
}

function makeTpl(patch) {
  return rebuildTplFromRaw(patch);
}

function rebuildTplFromRaw(raw) {
  const n = TPL * TPL;
  let sum = 0;
  for (let i = 0; i < n; i++) sum += raw[i];
  const mean = sum / n;
  const centered = new Float32Array(n);
  let e = 0;
  for (let i = 0; i < n; i++) {
    const c = raw[i] - mean;
    centered[i] = c;
    e += c * c;
  }
  if (e < 2500) return null;
  return { w: TPL, h: TPL, raw, centered, mean, sigma: Math.sqrt(e) };
}

function adaptTpl(gray, iw, ih, cx, cy, ncc) {
  if (!S.tpl || ncc < 0.82) return;
  const tlx = clamp(Math.round(cx - TPL * 0.5), 0, iw - TPL);
  const tly = clamp(Math.round(cy - TPL * 0.5), 0, ih - TPL);
  const patch = extractPatch(gray, iw, tlx, tly);
  const a = 0.08;
  const raw = S.tpl.raw;
  for (let i = 0; i < raw.length; i++) raw[i] = raw[i] * (1 - a) + patch[i] * a;
  const next = rebuildTplFromRaw(raw);
  if (next) S.tpl = next;
}

function nccAt(gray, iw, tlx, tly, tpl, step) {
  step = step || 1;
  const tw = tpl.w, th = tpl.h, raw = tpl.raw;
  let sI = 0, sI2 = 0, sT = 0, sT2 = 0, dot = 0, n = 0;
  for (let j = 0; j < th; j += step) {
    const row = (tly + j) * iw + tlx;
    const tr = j * tw;
    for (let i = 0; i < tw; i += step) {
      const iv = gray[row + i];
      const tv = raw[tr + i];
      sI += iv; sI2 += iv * iv;
      sT += tv; sT2 += tv * tv;
      dot += iv * tv;
      n++;
    }
  }
  if (n < 8) return -1;
  const num = n * dot - sI * sT;
  const denI = n * sI2 - sI * sI;
  const denT = n * sT2 - sT * sT;
  if (denI < 1e-4 || denT < 1e-4) return -1;
  return num / Math.sqrt(denI * denT);
}

function nccAtHalf(gray, iw, tlx, tly, tpl) {
  const tw = tpl.w, th = tpl.h, raw = tpl.raw;
  let sI = 0, sI2 = 0, sT = 0, sT2 = 0, dot = 0, n = 0;
  for (let j = 0; j < th - 1; j += 2) {
    const row = (tly + j) * iw + tlx;
    const row2 = row + iw;
    const tr = j * tw;
    const tr2 = tr + tw;
    for (let i = 0; i < tw - 1; i += 2) {
      const iv = 0.25 * (gray[row + i] + gray[row + i + 1] + gray[row2 + i] + gray[row2 + i + 1]);
      const tv = 0.25 * (raw[tr + i] + raw[tr + i + 1] + raw[tr2 + i] + raw[tr2 + i + 1]);
      sI += iv; sI2 += iv * iv;
      sT += tv; sT2 += tv * tv;
      dot += iv * tv;
      n++;
    }
  }
  if (n < 8) return -1;
  const num = n * dot - sI * sT;
  const denI = n * sI2 - sI * sI;
  const denT = n * sT2 - sT * sT;
  if (denI < 1e-4 || denT < 1e-4) return -1;
  return num / Math.sqrt(denI * denT);
}

function nccSearch(gray, iw, ih, tpl, tlMinX, tlMinY, tlMaxX, tlMaxY, stride) {
  const maxX = iw - tpl.w;
  const maxY = ih - tpl.h;
  let xa = clamp(Math.round(tlMinX), 0, maxX);
  let ya = clamp(Math.round(tlMinY), 0, maxY);
  let xb = clamp(Math.round(tlMaxX), 0, maxX);
  let yb = clamp(Math.round(tlMaxY), 0, maxY);
  if (xb < xa) { const t = xa; xa = xb; xb = t; }
  if (yb < ya) { const t = ya; ya = yb; yb = t; }
  const st = stride < 2 ? 1 : stride;
  const K = 5;
  const peaks = [];
  function consider(s, x, y) {
    if (peaks.length < K) { peaks.push({ s, x, y }); return; }
    let w = 0;
    for (let i = 1; i < peaks.length; i++) if (peaks[i].s < peaks[w].s) w = i;
    if (s > peaks[w].s) peaks[w] = { s, x, y };
  }
  const coarse = st > 1 ? nccAtHalf : nccAt;
  for (let y = ya; y <= yb; y += st) {
    for (let x = xa; x <= xb; x += st) {
      const s = coarse(gray, iw, x, y, tpl, st > 1 ? 2 : 1);
      consider(s, x, y);
    }
  }
  if (!peaks.length) consider(-2, xa, ya);
  let best = -2, bx = xa, by = ya;
  const r = st > 1 ? Math.max(st + 1, 5) : 1;
  for (const pk of peaks) {
    const x0 = Math.max(0, pk.x - r), x1 = Math.min(maxX, pk.x + r);
    const y0 = Math.max(0, pk.y - r), y1 = Math.min(maxY, pk.y + r);
    for (let y = y0; y <= y1; y++) {
      for (let x = x0; x <= x1; x++) {
        const s = nccAt(gray, iw, x, y, tpl, 1);
        if (s > best) { best = s; bx = x; by = y; }
      }
    }
  }
  return { ncc: best, x: bx, y: by };
}

function subpixelPeak(gray, iw, ih, tpl, px, py) {
  const maxX = iw - tpl.w, maxY = ih - tpl.h;
  const c = nccAt(gray, iw, px, py, tpl, 1);
  let dx = 0, dy = 0;
  if (px > 0 && px < maxX) {
    const cm = nccAt(gray, iw, px - 1, py, tpl, 1);
    const cp = nccAt(gray, iw, px + 1, py, tpl, 1);
    const d = cm - 2 * c + cp;
    if (Math.abs(d) > 1e-8) dx = clamp(0.5 * (cm - cp) / d, -1, 1);
  }
  if (py > 0 && py < maxY) {
    const cm = nccAt(gray, iw, px, py - 1, tpl, 1);
    const cp = nccAt(gray, iw, px, py + 1, tpl, 1);
    const d = cm - 2 * c + cp;
    if (Math.abs(d) > 1e-8) dy = clamp(0.5 * (cm - cp) / d, -1, 1);
  }
  return { x: px + dx + tpl.w * 0.5, y: py + dy + tpl.h * 0.5, ncc: c };
}

function surroundStats(gray, iw, ih, cx, cy, rad, step) {
  const x0 = clamp(Math.round(cx - rad), 0, iw - 1);
  const y0 = clamp(Math.round(cy - rad), 0, ih - 1);
  const x1 = clamp(Math.round(cx + rad), 0, iw - 1);
  const y1 = clamp(Math.round(cy + rad), 0, ih - 1);
  let n = 0, sum = 0, sum2 = 0;
  for (let y = y0; y <= y1; y += step) {
    for (let x = x0; x <= x1; x += step) {
      const v = gray[y * iw + x];
      sum += v; sum2 += v * v; n++;
    }
  }
  if (!n) return { mean: 0, vr: 0 };
  const mean = sum / n;
  return { mean, vr: sum2 / n - mean * mean };
}

function patchScore(img, gray, iw, ih, tlx, tly) {
  const d = img.data;
  let skin = 0, seen = 0, sum = 0, sum2 = 0;
  for (let j = 0; j < TPL; j += 2) {
    for (let i = 0; i < TPL; i += 2) {
      const p = ((tly + j) * iw + (tlx + i)) * 4;
      if (isSkinHSV(d[p], d[p + 1], d[p + 2])) skin++;
      seen++;
      const v = gray[(tly + j) * iw + (tlx + i)];
      sum += v; sum2 += v * v;
    }
  }
  const skinFrac = skin / seen;
  if (skinFrac > 0.38) return 0;
  const mean = sum / seen;
  const vr = sum2 / seen - mean * mean;
  if (vr < 55) return 0;
  const cx = tlx + TPL * 0.5, cy = tly + TPL * 0.5;
  const big = surroundStats(gray, iw, ih, cx, cy, TPL * 1.75, 4);
  const sd = Math.sqrt(Math.max(0, vr));
  const sdB = Math.sqrt(Math.max(0, big.vr));
  const distinct = Math.abs(mean - big.mean) + Math.abs(sd - sdB);
  if (distinct < 6 && vr < 140) return 0;
  return sd * (1 - skinFrac) * (0.35 + Math.min(1.6, distinct / 28));
}

function commitTpl(gray, iw, ih, tlx, tly, now) {
  tlx = clamp(tlx, 0, iw - TPL);
  tly = clamp(tly, 0, ih - TPL);
  const tpl = makeTpl(extractPatch(gray, iw, tlx, tly));
  if (!tpl) return false;
  S.tpl = tpl;
  S.lockTplAt = now;
  const cx = tlx + TPL * 0.5;
  const cy = tly + TPL * 0.5;
  resetTrackFilters();
  S.det = { x: cx, y: cy, conf: 1 };
  S.lastDetAt = now;
  S.lastRaw = { x: cx, y: cy };
  S.smooth = { x: cx, y: cy };
  S.ncc = 1;
  euroStep(S.euroX, now, cx, EURO_MINCUTOFF, EURO_BETA, EURO_DCUTOFF);
  euroStep(S.euroY, now, cy, EURO_MINCUTOFF, EURO_BETA, EURO_DCUTOFF);
  S.vel.x = 0; S.vel.y = 0; S.trackT = now;
  return true;
}

function findHand() {
  const skin = S.skin;
  if (!skin) return null;
  const iw = PROC_W, ih = PROC_H;
  const step = 2;
  const sw = (iw / step) | 0;
  const sh = (ih / step) | 0;
  const seen = new Uint8Array(sw * sh);
  const qx = new Int16Array(sw * sh);
  const qy = new Int16Array(sw * sh);
  const fx0 = (sw * 0.28) | 0, fx1 = (sw * 0.72) | 0, fy1 = (sh * 0.36) | 0;
  let best = null;
  for (let sy = 0; sy < sh; sy++) {
    for (let sx = 0; sx < sw; sx++) {
      const si = sy * sw + sx;
      if (seen[si] || !skin[(sy * step) * iw + (sx * step)]) continue;
      let head = 0, tail = 0;
      qx[tail] = sx; qy[tail] = sy; tail++;
      seen[si] = 1;
      let area = 0, sumx = 0, sumy = 0, faceHits = 0;
      let minx = sx, maxx = sx, miny = sy, maxy = sy;
      while (head < tail) {
        const cx = qx[head], cy = qy[head];
        head++;
        area++;
        sumx += cx; sumy += cy;
        if (cx < minx) minx = cx; if (cx > maxx) maxx = cx;
        if (cy < miny) miny = cy; if (cy > maxy) maxy = cy;
        if (cx >= fx0 && cx <= fx1 && cy <= fy1) faceHits++;
        const nbs = [cx - 1, cy, cx + 1, cy, cx, cy - 1, cx, cy + 1];
        for (let k = 0; k < 8; k += 2) {
          const nx = nbs[k], ny = nbs[k + 1];
          if (nx < 0 || ny < 0 || nx >= sw || ny >= sh) continue;
          const ni = ny * sw + nx;
          if (seen[ni] || !skin[(ny * step) * iw + (nx * step)]) continue;
          seen[ni] = 1;
          qx[tail] = nx; qy[tail] = ny; tail++;
        }
      }
      if (area < 55) continue;
      const bw = maxx - minx + 1, bh = maxy - miny + 1;
      const elong = Math.max(bw, bh) / Math.max(1, Math.min(bw, bh));
      const faceFrac = faceHits / area;
      if (faceFrac > 0.55 && elong < 1.4 && area > sw * sh * 0.07) continue;
      const score = area * (1.15 + elong) * (1 - faceFrac * 0.75);
      if (!best || score > best.score) {
        best = { area, score, elong, minx, maxx, miny, maxy, cx: sumx / area, cy: sumy / area };
      }
    }
  }
  if (!best) return null;
  const ccx = best.cx * step, ccy = best.cy * step;
  const x0 = Math.max(0, best.minx * step);
  const y0 = Math.max(0, best.miny * step);
  const x1 = Math.min(iw - 1, (best.maxx + 1) * step);
  const y1 = Math.min(ih - 1, (best.maxy + 1) * step);
  let tipx = ccx, tipy = ccy, bestD = -1;
  for (let y = y0; y <= y1; y += 2) {
    const row = y * iw;
    for (let x = x0; x <= x1; x += 2) {
      if (!skin[row + x]) continue;
      const dx = x - ccx, dy = y - ccy;
      const dist = dx * dx + dy * dy;
      if (dist > bestD) { bestD = dist; tipx = x; tipy = y; }
    }
  }
  let rx = tipx, ry = tipy, rd = bestD;
  for (let y = Math.max(0, tipy - 4); y <= Math.min(ih - 1, tipy + 4); y++) {
    const row = y * iw;
    for (let x = Math.max(0, tipx - 4); x <= Math.min(iw - 1, tipx + 4); x++) {
      if (!skin[row + x]) continue;
      const dx = x - ccx, dy = y - ccy;
      const dist = dx * dx + dy * dy;
      if (dist > rd) { rd = dist; rx = x; ry = y; }
    }
  }
  return {
    x: rx, y: ry, cx: ccx, cy: ccy,
    conf: clamp(best.score / 3800, 0.35, 1),
    area: best.area,
  };
}

function sampleLock(img, now) {
  const hand = findHand();
  if (!hand || hand.conf < 0.4) return;
  if (!S.lockHand) S.lockHand = { n: 0, x: 0, y: 0 };
  S.lockHand.n++;
  S.lockHand.x += hand.x;
  S.lockHand.y += hand.y;
  const elapsed = now - (S.lockStart || now);
  if (elapsed < LOCK_SAMPLE_MS) return;
  if (S.tpl) return;
  if (S.lockHand.n < 6) return;
  const cx = S.lockHand.x / S.lockHand.n;
  const cy = S.lockHand.y / S.lockHand.n;
  commitTpl(S.gray, PROC_W, PROC_H, Math.round(cx - TPL * 0.5), Math.round(cy - TPL * 0.5), now);
}

function applyEuroPoint(now, x, y) {
  const same = S.lastRaw && Math.abs(x - S.lastRaw.x) < 1e-4 && Math.abs(y - S.lastRaw.y) < 1e-4;
  const dtEuro = S.euroX.ready ? now - S.euroX.t : 9999;
  S.lastRaw = { x, y };
  if (same && dtEuro < 20) { S.trackT = now; return; }
  const fx = euroStep(S.euroX, now, x, EURO_MINCUTOFF, EURO_BETA, EURO_DCUTOFF);
  const fy = euroStep(S.euroY, now, y, EURO_MINCUTOFF, EURO_BETA, EURO_DCUTOFF);
  S.smooth = { x: fx, y: fy };
  S.vel.x = S.euroX.dx;
  S.vel.y = S.euroY.dx;
  S.trackT = now;
}

function nccTrack(now) {
  const gray = S.gray;
  const iw = PROC_W, ih = PROC_H;
  const tpl = S.tpl;
  const age = now - (S.lastDetAt || 0);
  const pred = predictedCam(now) || S.smooth;
  const half = TPL * 0.5;
  let x0, y0, x1, y1, stride;
  if (pred && age <= 350) {
    const rad = SEARCH_R + (age > COAST_MS ? 36 : 0);
    const tlx = pred.x - half, tly = pred.y - half;
    x0 = tlx - rad; y0 = tly - rad;
    x1 = tlx + rad; y1 = tly + rad;
    stride = 2;
  } else {
    x0 = 0; y0 = 0; x1 = iw; y1 = ih;
    stride = 4;
  }
  const hit = nccSearch(gray, iw, ih, tpl, x0, y0, x1, y1, stride);
  const sub = subpixelPeak(gray, iw, ih, tpl, hit.x, hit.y);
  S.ncc = sub.ncc;
  const maxX = iw - tpl.w, maxY = ih - tpl.h;
  const onBorder = hit.x <= 1 || hit.y <= 1 || hit.x >= maxX - 1 || hit.y >= maxY - 1;
  let accept = sub.ncc >= NCC_GOOD;
  if (onBorder && sub.ncc < 0.78) accept = false;
  if (accept && pred && S.euroX && S.euroX.ready && age <= 350) {
    const jump = Math.hypot(sub.x - pred.x, sub.y - pred.y);
    if (jump > OUTLIER_FRAC * PROC_W) accept = false;
  }
  if (accept) {
    S.det = { x: sub.x, y: sub.y, conf: clamp(sub.ncc, 0, 1) };
    S.lastDetAt = now;
    applyEuroPoint(now, sub.x, sub.y);
    adaptTpl(gray, iw, ih, sub.x, sub.y, sub.ncc);
  } else {
    S.det = null;
    coastTrack(now);
    if (age > QUALITY_LOST_MS) resetTrackFilters();
  }
}

function detGood() { return S.det && S.det.conf >= NCC_GOOD; }

function indexExtended(lm) {
  const w = lm[0], pip = lm[6], tip = lm[8];
  if (!w || !pip || !tip) return false;
  const dTip = Math.hypot(tip.x - w.x, tip.y - w.y);
  const dPip = Math.hypot(pip.x - w.x, pip.y - w.y);
  return dTip > dPip * 1.06;
}

function handPointScore(lm) {
  if (!lm || !lm[8]) return -1;
  let s = indexExtended(lm) ? 2.4 : 0.2;
  s += (1 - lm[8].y) * 1.2;
  if (lm[0]) s += Math.max(0, lm[0].y - lm[8].y);
  return s;
}

function bestHand(landmarks) {
  let best = null, bestS = -1;
  for (let i = 0; i < landmarks.length; i++) {
    const s = handPointScore(landmarks[i]);
    if (s > bestS) { bestS = s; best = landmarks[i]; }
  }
  return best;
}

function nailMuzzle(lm) {
  const pip = lm[6], tip = lm[8];
  const nx = tip.x + (tip.x - pip.x) * 0.18;
  const ny = tip.y + (tip.y - pip.y) * 0.18;
  return {
    x: (1 - nx) * (PROC_W - 1),
    y: ny * (PROC_H - 1),
  };
}

function pinchStrength(lm) {
  const thumb = lm[4], index = lm[8], wrist = lm[0], palm = lm[9];
  if (!thumb || !index) return 0;
  const scale = (wrist && palm)
    ? Math.hypot(wrist.x - palm.x, wrist.y - palm.y)
    : 0.2;
  const d = Math.hypot(thumb.x - index.x, thumb.y - index.y) / Math.max(0.08, scale);
  return clamp(1 - (d - 0.28) / 0.4, 0, 1);
}

function applyMpLandmarks(lms, now) {
  if (!lms || !lms.length) return false;
  const lm = bestHand(lms);
  if (!lm || !lm[8] || !lm[6]) return false;
  const muz = nailMuzzle(lm);
  S.det = { x: muz.x, y: muz.y, conf: indexExtended(lm) ? 0.92 : 0.4 };
  S.lastDetAt = now;
  applyEuroPoint(now, muz.x, muz.y);
  S.tpl = { w: TPL, h: TPL, fromHands: true };
  S.lockTplAt = now;
  S.ncc = S.det.conf;
  S.handLm = lm;
  return true;
}

function onHandsWorkerMsg(ev) {
  const msg = ev.data || {};
  if (msg.type === "result") {
    S.mpBusy = false;
    if (msg.delegate) S.mpDelegate = msg.delegate;
    applyMpLandmarks(msg.landmarks, performance.now());
    return;
  }
  if (msg.type === "fail") {
    S.mpBusy = false;
    console.warn("HandLandmarker worker fail", msg.error);
  }
}

function onHandsWorkerErr(ev) {
  S.mpBusy = false;
  console.warn("HandLandmarker worker error", ev && ev.message);
}

function kickWorkerDetect(now) {
  if (!S.hands || !S.hands.worker || S.mpBusy || !cam.videoWidth) return;
  if (proc.width !== PROC_W) sizeProc();
  const ts = Math.max((S.mpTs || 0) + 1, now);
  S.mpTs = ts;
  S.mpBusy = true;
  const w = PROC_W;
  const h = PROC_H || Math.max(1, Math.round(PROC_W * cam.videoHeight / cam.videoWidth));
  const post = (bmp) => {
    if (!S.hands || !S.hands.worker) {
      if (bmp && bmp.close) bmp.close();
      S.mpBusy = false;
      return;
    }
    try {
      S.hands.worker.postMessage({ type: "frame", bitmap: bmp, ts }, [bmp]);
    } catch (e) {
      try { if (bmp && bmp.close) bmp.close(); } catch (e2) { /* closed */ }
      S.mpBusy = false;
    }
  };
  if (typeof createImageBitmap !== "function") {
    S.mpBusy = false;
    return;
  }
  createImageBitmap(cam, { resizeWidth: w, resizeHeight: h, resizeQuality: "low" }).then(post).catch(() => {
    S.mpBusy = false;
  });
}

function mpTrackMain(now) {
  if (!S.hands || typeof S.hands.detectForVideo !== "function" || !cam.videoWidth) return false;
  if (proc.width !== PROC_W) sizeProc();
  const ts = Math.max((S.mpTs || 0) + 1, now);
  S.mpTs = ts;
  let res;
  try {
    res = S.hands.detectForVideo(cam, ts);
  } catch (e) {
    return false;
  }
  return applyMpLandmarks(res && res.landmarks, now);
}

function mpTrack(now) {
  if (!S.handsOn || !S.hands || !cam.videoWidth) return false;
  if (S.hands.worker) return kickAndFresh(now);
  return mpTrackMain(now);
}

function kickAndFresh(now) {
  kickWorkerDetect(now);
  return !!(S.det && (now - (S.lastDetAt || 0) < 80));
}

function maybePinchFire(lm) {
  if (!lm) { S.pinchHeld = false; return; }
  const p = pinchStrength(lm);
  if (p > 0.72 && !S.pinchHeld && indexExtended(lm)) {
    S.pinchHeld = true;
    if (phase === "range" || phase === "bay") fire();
    else if (phase === "calibrate" && S.calibIndex >= 4) fire();
  } else if (p < 0.35) {
    S.pinchHeld = false;
  }
}

function armVideoTrack() {
  if (!S.handsOn || S.rvfc || !cam.requestVideoFrameCallback) return;
  S.rvfc = true;
  const tick = (now) => {
    if (!camReady || !S.handsOn) { S.rvfc = false; return; }
    mpTrack(now);
    cam.requestVideoFrameCallback(tick);
  };
  cam.requestVideoFrameCallback(tick);
}

function handsModelTries() {
  const cdn = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21";
  const here = new URL("./", import.meta.url);
  return [
    {
      js: new URL("./vendor/mediapipe/vision_bundle.mjs", here).href,
      wasm: new URL("./vendor/mediapipe/wasm", here).href,
      model: new URL("./vendor/mediapipe/hand_landmarker.task", here).href,
    },
    {
      js: cdn + "/vision_bundle.mjs",
      wasm: cdn + "/wasm",
      model: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    },
  ];
}

function startHandsWorker() {
  return new Promise((resolve, reject) => {
    let worker;
    try {
      worker = new Worker(new URL("./hands_worker.js", import.meta.url), { type: "module" });
    } catch (e) {
      reject(e);
      return;
    }
    const timer = setTimeout(() => {
      try { worker.terminate(); } catch (e) { /* already dead */ }
      reject(new Error("hands worker init timeout"));
    }, 20000);
    const fail = (err) => {
      clearTimeout(timer);
      try { worker.terminate(); } catch (e) { /* already dead */ }
      reject(err);
    };
    worker.onerror = (ev) => {
      fail(ev.error || new Error(ev.message || "hands worker error"));
    };
    worker.onmessage = (ev) => {
      const msg = ev.data || {};
      if (msg.type === "ready") {
        clearTimeout(timer);
        S.hands = { worker };
        S.mpDelegate = msg.delegate || "GPU";
        S.mpBusy = false;
        S.handsOn = true;
        S.engine.hands = true;
        worker.onmessage = onHandsWorkerMsg;
        worker.onerror = onHandsWorkerErr;
        resolve(true);
        return;
      }
      if (msg.type === "fail") {
        fail(new Error(msg.error || "hands worker fail"));
      }
    };
    worker.postMessage({ type: "init", tries: handsModelTries() });
  });
}

async function initHandsMain() {
  const tries = handsModelTries();
  const base = { runningMode: "VIDEO", numHands: 2, minHandDetectionConfidence: 0.45, minHandPresenceConfidence: 0.45, minTrackingConfidence: 0.45 };
  for (const t of tries) {
    try {
      const mod = await import(t.js);
      const vision = await mod.FilesetResolver.forVisionTasks(t.wasm);
      try {
        S.hands = await mod.HandLandmarker.createFromOptions(vision, Object.assign({ baseOptions: { modelAssetPath: t.model, delegate: "GPU" } }, base));
        S.mpDelegate = "GPU";
      } catch (e) {
        S.hands = await mod.HandLandmarker.createFromOptions(vision, Object.assign({ baseOptions: { modelAssetPath: t.model, delegate: "CPU" } }, base));
        S.mpDelegate = "CPU";
      }
      S.handsOn = true;
      S.engine.hands = true;
      return true;
    } catch (e) {
      console.warn("HandLandmarker try failed", t.js, e);
    }
  }
  S.handsOn = false;
  S.engine.hands = false;
  return false;
}

let handsPromise = null;
async function initHands() {
  if (handsPromise) return handsPromise;
  handsPromise = initHandsInner();
  return handsPromise;
}
async function initHandsInner() {
  try {
    return await startHandsWorker();
  } catch (e) {
    console.warn("HandLandmarker worker failed, main-thread last resort", e);
    return initHandsMain();
  }
}

function fallbackSkin(now) {
  S.handLm = null;
  S.pinchHeld = false;
  if (S.tpl && S.tpl.fromHands) S.tpl = null;
  if (!S.skin || !S.gray) return false;
  const hand = findHand();
  if (hand && hand.conf >= 0.42) {
    S.det = { x: hand.x, y: hand.y, conf: hand.conf };
    S.lastDetAt = now;
    applyEuroPoint(now, hand.x, hand.y);
    if (!S.tpl) {
      commitTpl(S.gray, PROC_W, PROC_H, Math.round(hand.x - TPL * 0.5), Math.round(hand.y - TPL * 0.5), now);
    }
    return true;
  }
  if (S.tpl && !S.tpl.fromHands) {
    nccTrack(now);
    return !!S.det;
  }
  sampleLock(S.frame, now);
  return !!S.det;
}

function runTrack(now) {
  if (!S.euroX) resetTrackFilters();
  const stamp = cam.currentTime;
  const mpFresh = S.handsOn && S.det && (now - (S.lastDetAt || 0) < 80);
  if (stamp && stamp === S.camStamp) {
    if (!mpFresh) {
      if (!fallbackSkin(now) && !S.det) coastTrack(now);
    } else if (!S.det) coastTrack(now);
    updateQuality(now, S.det);
    return;
  }
  S.camStamp = stamp;
  if (S.handsOn) {
    if (S.rvfc && (now - (S.lastDetAt || 0) < 120)) {
      if (!S.det) coastTrack(now);
    } else if (mpTrack(now)) {
      S.mpMiss = 0;
    } else {
      S.mpMiss = (S.mpMiss || 0) + 1;
      if (!fallbackSkin(now)) {
        S.det = null;
        coastTrack(now);
        if (now - (S.lastDetAt || 0) > QUALITY_LOST_MS) resetTrackFilters();
      }
    }
  } else if (!fallbackSkin(now)) {
    if (!S.det) coastTrack(now);
  }
  updateQuality(now, S.det);
}
// --- Frame Capture from Camera Sink ---
function sizeProc() {
  if (!cam.videoWidth) return;
  const aspect = cam.videoWidth / cam.videoHeight;
  PROC_H = Math.round(PROC_W / aspect);
  proc.width = PROC_W;
  proc.height = PROC_H;
  S.gray = new Uint8Array(PROC_W * PROC_H);
  S.skin = new Uint8Array(PROC_W * PROC_H);
}

function grabFrame() {
  if (!camReady || !cam.videoWidth) return false;
  if (proc.width !== PROC_W) sizeProc();
  const mpFresh = S.handsOn && S.det && (performance.now() - (S.lastDetAt || 0) < 80);
  if (mpFresh) return true;
  pctx.drawImage(cam, 0, 0, PROC_W, PROC_H);
  const img = pctx.getImageData(0, 0, PROC_W, PROC_H);
  S.frame = img;
  const d = img.data;
  const gray = S.gray;
  const skin = S.skin;
  for (let i = 0, j = 0; i < d.length; i += 4, j++) {
    const r = d[i], g = d[i + 1], b = d[i + 2];
    gray[j] = (r * 77 + g * 150 + b * 29) >> 8;
    skin[j] = isSkinByte(r, g, b);
  }
  return true;
}

export {
  PROC_W,
  LOCK_SAMPLE_MS,
  LOCK_CONFIRM_MS,
  LOCK_GIVE_MS,
  TPL_FAIL_MS,
  COAST_MS,
  OUTLIER_FRAC,
  QUALITY_LOST_MS,
  TPL,
  NCC_GOOD,
  SEARCH_R,
  FIND_STEP,
  EURO_MINCUTOFF,
  EURO_BETA,
  EURO_DCUTOFF,
  euroAlpha,
  makeEuro,
  euroStep,
  resetTrackFilters,
  coastTrack,
  updateQuality,
  predictedCam,
  isSkinByte,
  isSkinHSV,
  extractPatch,
  makeTpl,
  rebuildTplFromRaw,
  adaptTpl,
  nccAt,
  nccAtHalf,
  nccSearch,
  subpixelPeak,
  surroundStats,
  patchScore,
  commitTpl,
  findHand,
  sampleLock,
  applyEuroPoint,
  nccTrack,
  detGood,
  indexExtended,
  handPointScore,
  bestHand,
  nailMuzzle,
  pinchStrength,
  applyMpLandmarks,
  onHandsWorkerMsg,
  kickWorkerDetect,
  mpTrackMain,
  mpTrack,
  maybePinchFire,
  armVideoTrack,
  initHands,
  fallbackSkin,
  runTrack,
  sizeProc,
  grabFrame,
};
