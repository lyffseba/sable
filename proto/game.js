/* LiftShot — physical-aim shooter
   Webcam locks a patch of the mouse body (like a Superlight sensor locks the mat).
   NCC track → One Euro → 4-corner homography. Face never drawn. */
"use strict";

const $ = (id) => document.getElementById(id);
const cam = $("cam");
const proc = $("proc");
const canvas = $("game");
const ctx = canvas.getContext("2d", { alpha: false });
const pctx = proc.getContext("2d", { willReadFrequently: true, alpha: false });

const screens = {
  boot: $("screen-boot"),
  lock: $("screen-lock"),
  calibrate: $("screen-calib"),
  range: $("screen-range"),
  results: $("screen-results"),
};
const PROC_W = 480;
const CROP_TOP = 0.30;
const HID_IDLE_MS = 40;
const RANGE_MS = 60000;
const HUD_PAD = 16;
const CORNER_NAMES = ["TOP LEFT", "TOP RIGHT", "BOTTOM RIGHT", "BOTTOM LEFT"];
const LOCK_SAMPLE_MS = 1200;
const LOCK_CONFIRM_MS = 200;
const TPL_FAIL_MS = 2200;
const COAST_MS = 100;
const OUTLIER_FRAC = 0.18;
const QUALITY_LOST_MS = 280;
const TPL = 48;
const NCC_GOOD = 0.58;
const SEARCH_R = 56;
const FIND_STEP = 8;
// Pointing, not soup. fcmin=1Hz is ~160ms lag at 30fps — the reticle trails the Superlight.
const EURO_MINCUTOFF = 3.0, EURO_BETA = 0.03, EURO_DCUTOFF = 1.0;
const LIFT_ON_MS = 50;
let W = 1280, H = 720, dpr = 1, PROC_H = 270, phase = "boot";
let stream = null, camReady = false, lastT = 0;
const S = {
  det: null, smooth: null, vel: { x: 0, y: 0 }, lastDetAt: 0, trackT: 0,
  camStamp: -1, quality: 0, euroX: null, euroY: null, lastRaw: null, seeking: false,
  H: null, useBilinear: false, camPts: [null, null, null, null], calibIndex: 0,
  calibFlash: 0, forceGun: false, desktop: false, hidLast: 0, hidMoving: false,
  mode: "PAD", lifted: false, liftMs: 0, liftTick: 0, aim: { x: 0.5, y: 0.5 }, recoil: 0, punch: 0, flash: 0, hitstop: 0,
  orbs: [], parts: [], pops: [], score: 0, hits: 0, shots: 0, combo: 0, comboMax: 0,
  rangeStart: 0, lockSince: 0, locked: false, lockStart: 0, lockAdvance: false,
  noLockFlash: 0, liftPulse: 0, enteringRange: false,
  tpl: null, ncc: 0, gray: null,
  lockAcc: null, lockAccCols: 0, lockAccRows: 0,
  lockBestScore: 0, lockBestPatch: null, lockBestTL: null, lockTplAt: 0,
};
function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
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

function predictedCam(now) {
  if (!S.smooth) return null;
  const dt = Math.max(0, (now - (S.trackT || now)) * 0.001);
  return { x: S.smooth.x + S.vel.x * dt, y: S.smooth.y + S.vel.y * dt };
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
function solveLinear(A, b) {
  const n = b.length;
  const M = new Array(n);
  for (let i = 0; i < n; i++) { M[i] = A[i].slice(); M[i].push(b[i]); }
  for (let k = 0; k < n; k++) {
    let piv = k;
    for (let i = k + 1; i < n; i++) {
      if (Math.abs(M[i][k]) > Math.abs(M[piv][k])) piv = i;
    }
    if (Math.abs(M[piv][k]) < 1e-10) return null;
    if (piv !== k) { const tmp = M[k]; M[k] = M[piv]; M[piv] = tmp; }
    const diag = M[k][k];
    for (let j = k; j <= n; j++) M[k][j] /= diag;
    for (let i = 0; i < n; i++) {
      if (i === k) continue;
      const f = M[i][k];
      if (f === 0) continue;
      for (let j = k; j <= n; j++) M[i][j] -= f * M[k][j];
    }
  }
  return M.map((row) => row[n]);
}

function dltHomography(src, dst) {
  const A = [], b = [];
  for (let i = 0; i < 4; i++) {
    const x = src[i].x, y = src[i].y, u = dst[i].x, v = dst[i].y;
    A.push([x, y, 1, 0, 0, 0, -x * u, -y * u]); b.push(u);
    A.push([0, 0, 0, x, y, 1, -x * v, -y * v]); b.push(v);
  }
  const h = solveLinear(A, b);
  if (!h) return null;
  return [[h[0], h[1], h[2]], [h[3], h[4], h[5]], [h[6], h[7], 1]];
}

function applyH(Hm, x, y) {
  const w = Hm[2][0] * x + Hm[2][1] * y + Hm[2][2];
  if (Math.abs(w) < 1e-8) return null;
  return {
    x: (Hm[0][0] * x + Hm[0][1] * y + Hm[0][2]) / w,
    y: (Hm[1][0] * x + Hm[1][1] * y + Hm[1][2]) / w,
  };
}
function barycentric(p, a, b, c) {
  const v0x = b.x - a.x, v0y = b.y - a.y;
  const v1x = c.x - a.x, v1y = c.y - a.y;
  const v2x = p.x - a.x, v2y = p.y - a.y;
  const den = v0x * v1y - v1x * v0y;
  if (Math.abs(den) < 1e-12) return null;
  const v = (v2x * v1y - v1x * v2y) / den;
  const w = (v0x * v2y - v2x * v0y) / den;
  return { u: 1 - v - w, v, w };
}

function quadMap(p, src, dst) {
  const [A, B, C, D] = src;
  const [A2, B2, C2, D2] = dst;
  let bar = barycentric(p, A, B, C);
  if (bar && bar.u >= -0.08 && bar.v >= -0.08 && bar.w >= -0.08) {
    return { x: bar.u * A2.x + bar.v * B2.x + bar.w * C2.x, y: bar.u * A2.y + bar.v * B2.y + bar.w * C2.y };
  }
  bar = barycentric(p, A, C, D);
  if (bar) return { x: bar.u * A2.x + bar.v * C2.x + bar.w * D2.x, y: bar.u * A2.y + bar.v * C2.y + bar.w * D2.y };
  bar = barycentric(p, A, B, C);
  if (!bar) return { x: W / 2, y: H / 2 };
  return { x: bar.u * A2.x + bar.v * B2.x + bar.w * C2.x, y: bar.u * A2.y + bar.v * B2.y + bar.w * C2.y };
}

function screenCorners() {
  const m = Math.round(Math.min(W, H) * 0.085);
  return [{ x: m, y: m }, { x: W - m, y: m }, { x: W - m, y: H - m }, { x: m, y: H - m }];
}

function computeH() {
  if (!S.camPts.every(Boolean)) { S.H = null; return; }
  const src = S.camPts, dst = screenCorners();
  const Hm = dltHomography(src, dst);
  let bilinear = !Hm;
  if (Hm) {
    let maxErr = 0;
    for (let i = 0; i < 4; i++) {
      const p = applyH(Hm, src[i].x, src[i].y);
      if (!p) { bilinear = true; break; }
      const e = Math.hypot(p.x - dst[i].x, p.y - dst[i].y);
      if (e > maxErr) maxErr = e;
    }
    if (maxErr > 10) bilinear = true;
  }
  S.H = Hm; S.useBilinear = bilinear;
}

function camToScreen(cx, cy) {
  const p = { x: cx, y: cy };
  let out = null;
  if (S.H && !S.useBilinear) out = applyH(S.H, cx, cy);
  if (!out) out = quadMap(p, S.camPts, screenCorners());
  if (!out || !isFinite(out.x) || !isFinite(out.y)) return { x: S.aim.x, y: S.aim.y, lost: true };
  // Homography blow-up used to clamp into a screen corner. Freeze instead.
  if (out.x < -64 || out.x > W + 64 || out.y < -64 || out.y > H + 64) {
    return { x: S.aim.x, y: S.aim.y, lost: true };
  }
  return { x: clamp(out.x, 8, W - 8), y: clamp(out.y, 8, H - 8), lost: false };
}
const AU = { ctx: null, master: null, unlocked: false, droneGain: null };

function unlockAudio() {
  if (AU.unlocked) return;
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  AU.ctx = new AC();
  AU.master = AU.ctx.createGain();
  AU.master.gain.value = 0.32;
  AU.master.connect(AU.ctx.destination);
  AU.unlocked = true;
  startDrone();
  if (AU.ctx.state === "suspended") AU.ctx.resume();
}

function envGain(t, a, d, peak) {
  const g = AU.ctx.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(peak, t + a);
  g.gain.exponentialRampToValueAtTime(0.0001, t + a + d);
  return g;
}

function noiseBuffer(dur) {
  const n = Math.floor(AU.ctx.sampleRate * dur);
  const buf = AU.ctx.createBuffer(1, n, AU.ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
  return buf;
}

function bang() {
  if (!AU.unlocked) return;
  const t = AU.ctx.currentTime;
  const osc = AU.ctx.createOscillator();
  osc.type = "square";
  osc.frequency.setValueAtTime(180, t);
  osc.frequency.exponentialRampToValueAtTime(55, t + 0.09);
  const og = envGain(t, 0.004, 0.09, 0.22);
  osc.connect(og); og.connect(AU.master);
  osc.start(t); osc.stop(t + 0.11);
  const src = AU.ctx.createBufferSource();
  src.buffer = noiseBuffer(0.08);
  const bp = AU.ctx.createBiquadFilter();
  bp.type = "bandpass";
  bp.frequency.value = 1400;
  bp.Q.value = 0.7;
  const ng = envGain(t, 0.002, 0.055, 0.28);
  src.connect(bp); bp.connect(ng); ng.connect(AU.master);
  src.start(t);
}
function hitBlip(combo) {
  if (!AU.unlocked) return;
  const t = AU.ctx.currentTime;
  const f = 520 * Math.pow(1.08, Math.min(combo, 12));
  const osc = AU.ctx.createOscillator();
  osc.type = "sine";
  osc.frequency.setValueAtTime(f, t);
  osc.frequency.exponentialRampToValueAtTime(f * 1.35, t + 0.07);
  const g = envGain(t, 0.004, 0.09, 0.2);
  osc.connect(g); g.connect(AU.master);
  osc.start(t); osc.stop(t + 0.12);
}

function missTick() {
  if (!AU.unlocked) return;
  const t = AU.ctx.currentTime;
  const src = AU.ctx.createBufferSource();
  src.buffer = noiseBuffer(0.04);
  const bp = AU.ctx.createBiquadFilter();
  bp.type = "highpass";
  bp.frequency.value = 2800;
  const g = envGain(t, 0.001, 0.03, 0.12);
  src.connect(bp); bp.connect(g); g.connect(AU.master);
  src.start(t);
}

function startDrone() {
  const t = AU.ctx.currentTime;
  AU.droneGain = AU.ctx.createGain();
  AU.droneGain.gain.value = 0.028;
  AU.droneGain.connect(AU.master);
  [52, 78, 104].forEach((f, i) => {
    const o = AU.ctx.createOscillator();
    o.type = i === 2 ? "triangle" : "sine";
    o.frequency.value = f;
    const g = AU.ctx.createGain();
    g.gain.value = i === 0 ? 0.7 : 0.35;
    const lfo = AU.ctx.createOscillator();
    const lg = AU.ctx.createGain();
    lfo.frequency.value = 0.07 + i * 0.03;
    lg.gain.value = 1.6;
    lfo.connect(lg); lg.connect(o.frequency);
    o.connect(g); g.connect(AU.droneGain);
    o.start(t); lfo.start(t);
  });
}
function sizeProc() {
  const vw = cam.videoWidth || 1280;
  const vh = cam.videoHeight || 720;
  const cropH = vh * (1 - CROP_TOP);
  PROC_H = Math.max(140, Math.round(PROC_W * cropH / vw));
  proc.width = PROC_W;
  proc.height = PROC_H;
}

function grabFrame() {
  if (!camReady || cam.readyState < 2) return false;
  if (proc.width !== PROC_W || proc.height !== PROC_H) sizeProc();
  const vw = cam.videoWidth;
  const vh = cam.videoHeight;
  const sy = vh * CROP_TOP;
  const sh = vh * (1 - CROP_TOP);
  pctx.save();
  pctx.setTransform(-1, 0, 0, 1, PROC_W, 0);
  pctx.drawImage(cam, 0, sy, vw, sh, 0, 0, PROC_W, PROC_H);
  pctx.restore();
  return true;
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

function toGray(img) {
  const d = img.data, n = img.width * img.height;
  if (!S.gray || S.gray.length !== n) S.gray = new Float32Array(n);
  const g = S.gray;
  for (let i = 0, p = 0; i < n; i++, p += 4) {
    g[i] = 0.299 * d[p] + 0.587 * d[p + 1] + 0.114 * d[p + 2];
  }
  return g;
}

function extractPatch(gray, iw, tlx, tly) {
  const p = new Float32Array(TPL * TPL);
  for (let j = 0; j < TPL; j++) {
    const src = (tly + j) * iw + tlx;
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

function sampleLock(img, now) {
  const gray = S.gray;
  const iw = PROC_W, ih = PROC_H;
  if (iw < TPL + 4 || ih < TPL + 4) return;
  const cols = Math.max(1, Math.floor((iw - TPL) / FIND_STEP));
  const rows = Math.max(1, Math.floor((ih - TPL) / FIND_STEP));
  if (!S.lockAcc || S.lockAccCols !== cols || S.lockAccRows !== rows) {
    S.lockAcc = new Float32Array(cols * rows);
    S.lockAccCols = cols;
    S.lockAccRows = rows;
  }
  const acc = S.lockAcc;
  for (let i = 0; i < acc.length; i++) acc[i] *= 0.96;
  for (let gy = 0; gy < rows; gy++) {
    const tly = gy * FIND_STEP;
    for (let gx = 0; gx < cols; gx++) {
      const tlx = gx * FIND_STEP;
      acc[gy * cols + gx] += patchScore(img, gray, iw, ih, tlx, tly);
    }
  }
  const elapsed = now - (S.lockStart || now);
  if (elapsed < LOCK_SAMPLE_MS) return;
  if (S.tpl) return;

  let best = -1, bx = 0, by = 0;
  for (let i = 0; i < acc.length; i++) {
    if (acc[i] > best) { best = acc[i]; bx = i % cols; by = (i / cols) | 0; }
  }
  const sorted = Array.from(acc);
  sorted.sort((a, b) => a - b);
  const med = sorted[(sorted.length / 2) | 0];
  if (best < 12 || best < med * 2.2 + 6) return;

  let high = 0, minx = cols, maxx = 0, miny = rows, maxy = 0;
  const thresh = best * 0.72;
  for (let gy = 0; gy < rows; gy++) {
    for (let gx = 0; gx < cols; gx++) {
      if (acc[gy * cols + gx] >= thresh) {
        high++;
        if (gx < minx) minx = gx; if (gx > maxx) maxx = gx;
        if (gy < miny) miny = gy; if (gy > maxy) maxy = gy;
      }
    }
  }
  const bboxW = (maxx - minx + 1) * FIND_STEP;
  const bboxH = (maxy - miny + 1) * FIND_STEP;
  if (high > acc.length * 0.32) return;
  if (bboxW > iw * 0.62 && bboxH > ih * 0.62) return;

  commitTpl(gray, iw, ih, bx * FIND_STEP, by * FIND_STEP, now);
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

function runTrack(now) {
  if (!S.euroX) resetTrackFilters();
  const stamp = cam.currentTime;
  if (stamp && stamp === S.camStamp) {
    if (!S.det) coastTrack(now);
    updateQuality(now, S.det);
    return;
  }
  S.camStamp = stamp;
  S.det = null;
  const img = pctx.getImageData(0, 0, PROC_W, PROC_H);
  toGray(img);
  if (!S.tpl) {
    sampleLock(img, now);
    updateQuality(now, S.det);
    return;
  }
  nccTrack(now);
  updateQuality(now, S.det);
}

function detGood() { return !!S.det; }

function updateMode(now) {
  S.hidMoving = now - S.hidLast < HID_IDLE_MS;
  const since = S.lastDetAt ? now - S.lastDetAt : 1e9;
  const coasting = !!S.smooth && since <= COAST_MS;
  const locked = detGood() || coasting;
  const dtm = S.liftTick ? Math.min(40, now - S.liftTick) : 16;
  S.liftTick = now;
  if (S.desktop) {
    S.mode = "DESKTOP"; S.seeking = false; S.lifted = true; S.liftMs = LIFT_ON_MS; return;
  }
  const want = S.forceGun || (!S.hidMoving && locked);
  if (want) S.liftMs = Math.min(160, S.liftMs + dtm);
  else S.liftMs = Math.max(0, S.liftMs - dtm);
  S.lifted = S.forceGun || S.liftMs >= LIFT_ON_MS;
  if (S.forceGun) {
    S.mode = "GUN"; S.seeking = !locked; return;
  }
  if (S.hidMoving) {
    S.mode = "PAD"; S.seeking = !locked; return;
  }
  if (locked) {
    S.mode = "GUN"; S.seeking = false; return;
  }
  S.mode = "SEEKING"; S.seeking = true;
}
function publishAim(x, y) {
  if (!isFinite(x) || !isFinite(y)) return;
  S.aim.x = x; S.aim.y = y;
}
function updateAim() {
  if (S.desktop) return;
  if (!S.smooth) return;
  if (phase !== "range" && phase !== "calibrate") return;
  if (S.H || S.camPts.every(Boolean)) {
    const p = camToScreen(S.smooth.x, S.smooth.y);
    if (!p.lost) publishAim(p.x, p.y);
    else S.seeking = true;
  } else {
    publishAim((S.smooth.x / PROC_W) * W, (S.smooth.y / PROC_H) * H);
  }
}

async function enableCamera() {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return false;
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    cam.srcObject = stream;
    cam.setAttribute("playsinline", "");
    cam.muted = true;
    cam.setAttribute("aria-hidden", "true");
    if (!cam.videoWidth) {
      await new Promise((res) => {
        cam.onloadedmetadata = () => res();
        setTimeout(() => res(), 1500);
      });
    }
    await cam.play();
    camReady = true;
    sizeProc();
    return true;
  } catch (err) {
    camReady = false;
    return false;
  }
}

function goDesktopRange() {
  if (S.lockAdvance) return;
  S.lockAdvance = true;
  S.desktop = true;
  S.mode = "DESKTOP";
  setPhase("range");
}

function goCalib() {
  if (S.lockAdvance) return;
  S.lockAdvance = true;
  S.desktop = false;
  S.camPts = [null, null, null, null];
  S.H = null;
  setPhase("calibrate");
}

function resetLockState() {
  S.tpl = null; S.ncc = 0; S.det = null;
  S.lockAcc = null; S.lockBestScore = 0; S.lockBestPatch = null; S.lockBestTL = null;
  S.lockTplAt = 0; S.lockSince = 0; S.locked = false; S.lockAdvance = false;
  S.desktop = false; S.mode = "SEEKING"; S.smooth = null;
  S.lifted = false; S.liftMs = 0; S.liftTick = 0;
  resetTrackFilters();
}

async function play() {
  unlockAudio();
  $("btn-play").disabled = true;
  $("btn-play").textContent = "...";
  resetLockState();
  setPhase("lock");
  S.lockStart = performance.now();
  const ok = await enableCamera();
  if (!ok) {
    const st = $("lock-status");
    if (st) st.textContent = "SEEKING";
    return;
  }
  S.lockStart = performance.now();
}
function setPhase(next) {
  phase = next;
  for (const k of Object.keys(screens)) screens[k].hidden = k !== next;
  if (next === "calibrate") {
    S.calibIndex = S.camPts.every(Boolean) ? 4 : firstMissingCorner();
    updateCalibMsg();
    $("btn-redo").hidden = !S.camPts.some(Boolean) || S.calibIndex >= 4;
  }
  if (next === "range") startRange();
  if (next === "results") showResults();
}

function firstMissingCorner() {
  for (let i = 0; i < 4; i++) if (!S.camPts[i]) return i;
  return 4;
}

function updateCalibMsg() {
  const el = $("calib-msg");
  if (S.calibIndex < 4) el.textContent = "AIM AT " + CORNER_NAMES[S.calibIndex] + "  ·  CLICK TO CAPTURE";
  else el.textContent = "TEST AIM  ·  PUT ONE SHOT ON THE CENTER TARGET";
  $("btn-redo").hidden = !S.camPts.some(Boolean);
}

function startRange() {
  S.enteringRange = false;
  S.orbs = []; S.parts = []; S.pops = [];
  S.score = 0; S.hits = 0; S.shots = 0; S.combo = 0; S.comboMax = 0;
  S.rangeStart = performance.now();
  S.recoil = 0; S.punch = 0; S.flash = 0;
  spawnOrb({ x: W / 2, y: H * 0.46, r: 42, kind: "static", worth: 100, hue: 180, first: true });
}

function showResults() {
  const acc = S.shots ? Math.round((S.hits / S.shots) * 100) : 0;
  $("stats").innerHTML = [
    ["SCORE", S.score], ["HITS", S.hits], ["ACCURACY", acc + "%"],
    ["COMBO", S.comboMax], ["TIME", "60s"],
  ].map(([k, v]) => "<div class=\"stat\"><b>" + v + "</b><span>" + k + "</span></div>").join("");
}

function tickLock(t) {
  const st = $("lock-status");
  if (!camReady) {
    if (st) st.textContent = "SEEKING";
    return;
  }
  if (S.tpl && !detGood() && S.lockTplAt && t - S.lockTplAt > TPL_FAIL_MS) {
    S.tpl = null;
    S.lockAcc = null;
    S.lockStart = t;
    S.lockSince = 0;
    S.locked = false;
  }
  if (!S.tpl) {
    S.lockSince = 0;
    S.locked = false;
    if (st) st.textContent = (t - S.lockStart < LOCK_SAMPLE_MS) ? "LOCKING" : "SEEKING";
    return;
  }
  const coasting = !!S.smooth && (t - S.lastDetAt) <= COAST_MS;
  if (detGood() || coasting) {
    if (st) st.textContent = "MOUSE LOCKED";
    if (!S.lockSince) S.lockSince = t;
    S.locked = t - S.lockSince >= LOCK_CONFIRM_MS;
    if (S.locked) goCalib();
  } else {
    S.lockSince = 0;
    S.locked = false;
    if (st) st.textContent = "SEEKING";
  }
}
function spawnOrb(opts) {
  const o = Object.assign({
    x: 0, y: 0, r: 24, kind: "static", vx: 0, vy: 0,
    amp: 0, freq: 0, baseY: 0, phase: 0, worth: 100, hue: 185,
    life: 0, born: performance.now(), first: false,
  }, opts);
  S.orbs.push(o);
  return o;
}

function randomOrb(hard) {
  let x, y, r, guard = 0;
  const small = hard || Math.random() < 0.28;
  r = small ? 12 + Math.random() * 6 : 20 + Math.random() * 14;
  do {
    x = 70 + Math.random() * (W - 140);
    y = 80 + Math.random() * (H - 160);
    guard++;
  } while (nearOther(x, y, r + 36) && guard < 40);
  const roll = Math.random();
  let kind = "static";
  if (roll > 0.72) kind = "sine";
  else if (roll > 0.42) kind = "drift";
  const hue = small ? 318 : (Math.random() < 0.5 ? 185 : 162);
  const worth = small ? 250 : 100;
  return spawnOrb({
    x, y, r, kind, worth, hue,
    vx: kind === "drift" ? (Math.random() * 70 + 30) * (Math.random() < 0.5 ? -1 : 1) : 0,
    vy: kind === "drift" ? (Math.random() * 40 - 20) : 0,
    amp: kind === "sine" ? 18 + Math.random() * 28 : 0,
    freq: kind === "sine" ? 1.2 + Math.random() * 1.6 : 0,
    baseY: y, phase: Math.random() * Math.PI * 2,
  });
}

function nearOther(x, y, minD) {
  for (const o of S.orbs) {
    if (Math.hypot(o.x - x, o.y - y) < minD + o.r) return true;
  }
  return false;
}

function burst(x, y, hue, n) {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2;
    const sp = 80 + Math.random() * 280;
    S.parts.push({
      x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp,
      life: 0.35 + Math.random() * 0.35, age: 0,
      r: 1.5 + Math.random() * 2.8, hue,
    });
  }
}

function popup(x, y, text, hue) {
  S.pops.push({ x, y, text, hue, age: 0, life: 0.7 });
}

function desiredOrbCount(elapsed) {
  if (elapsed < 2000) return 1;
  if (elapsed < 12000) return 3;
  if (elapsed < 28000) return 5;
  if (elapsed < 45000) return 6;
  return 8;
}
function updateRange(dt, now) {
  const elapsed = now - S.rangeStart;
  if (elapsed >= RANGE_MS) { setPhase("results"); return; }
  const want = desiredOrbCount(elapsed);
  const hard = elapsed > 35000;
  while (S.orbs.length < want && (elapsed >= 2000 || S.orbs.length === 0)) randomOrb(hard);
  for (const o of S.orbs) {
    o.life += dt;
    if (o.kind === "drift") {
      o.x += o.vx * dt; o.y += o.vy * dt;
      if (o.x < o.r + 40 || o.x > W - o.r - 40) o.vx *= -1;
      if (o.y < o.r + 60 || o.y > H - o.r - 90) o.vy *= -1;
      o.x = clamp(o.x, o.r + 40, W - o.r - 40);
      o.y = clamp(o.y, o.r + 60, H - o.r - 90);
    } else if (o.kind === "sine") {
      o.phase += o.freq * dt;
      o.y = o.baseY + Math.sin(o.phase) * o.amp;
    }
  }
  for (const p of S.parts) {
    p.age += dt; p.x += p.vx * dt; p.y += p.vy * dt;
    p.vx *= 0.92; p.vy *= 0.92; p.vy += 40 * dt;
  }
  S.parts = S.parts.filter((p) => p.age < p.life);
  for (const p of S.pops) { p.age += dt; p.y -= 36 * dt; }
  S.pops = S.pops.filter((p) => p.age < p.life);
}

function fire() {
  if (phase !== "range" && !(phase === "calibrate" && S.calibIndex >= 4)) return;
  if (!S.desktop && S.smooth) {
    const now = performance.now();
    if (now - (S.trackT || 0) > 0) coastTrack(now);
    updateAim();
  }
  // Peek the mailbox. Lift is the trigger. Camera already wrote S.aim.
  if (!S.desktop && !S.lifted) return;
  bang();
  S.recoil = 2.2; S.flash = 0.04; S.punch = 1.6;
  if (phase === "calibrate") {
    S.shots++;
    const tx = W / 2, ty = H / 2;
    if (Math.hypot(S.aim.x - tx, S.aim.y - ty) < 46) {
      burst(tx, ty, 185, 18); hitBlip(1); S.hitstop = 1;
      if (!S.enteringRange) {
        S.enteringRange = true;
        setTimeout(() => { S.enteringRange = false; setPhase("range"); }, 420);
      }
    } else missTick();
    return;
  }
  S.shots++;
  let hit = null, best = 1e9;
  for (const o of S.orbs) {
    const d = Math.hypot(S.aim.x - o.x, S.aim.y - o.y);
    if (d < o.r + 7 && d < best) { best = d; hit = o; }
  }
  if (hit) {
    S.combo++;
    if (S.combo > S.comboMax) S.comboMax = S.combo;
    const pts = hit.worth * S.combo;
    S.score += pts; S.hits++;
    burst(hit.x, hit.y, hit.hue, 12 + ((Math.random() * 9) | 0));
    popup(hit.x, hit.y - hit.r, (S.combo > 1 ? S.combo + "x " : "") + pts, hit.hue);
    hitBlip(S.combo); S.hitstop = 1;
    S.orbs = S.orbs.filter((o) => o !== hit);
  } else { S.combo = 0; missTick(); }
}

function captureCorner() {
  let pt = null;
  const now = performance.now();
  const coasting = S.smooth && (now - S.lastDetAt) <= COAST_MS;
  if (S.smooth && (S.det || S.forceGun || coasting)) pt = { x: S.smooth.x, y: S.smooth.y };
  else if (S.desktop) {
    const c = screenCorners()[S.calibIndex];
    pt = { x: (c.x / W) * PROC_W, y: (c.y / H) * PROC_H };
  }
  if (!pt) { S.noLockFlash = 0.5; return; }
  S.camPts[S.calibIndex] = pt;
  S.calibFlash = 0.25;
  computeH();
  S.calibIndex = firstMissingCorner();
  if (S.calibIndex >= 4) S.calibIndex = 4;
  updateCalibMsg();
}
function fit() {
  W = window.innerWidth;
  H = window.innerHeight;
  dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  canvas.style.width = W + "px";
  canvas.style.height = H + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (S.camPts.every(Boolean)) computeH();
}

function bg() {
  ctx.fillStyle = "#050508";
  ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(W * 0.5, H * 0.42, 40, W * 0.5, H * 0.5, Math.max(W, H) * 0.72);
  g.addColorStop(0, "#0b1522");
  g.addColorStop(1, "#050508");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

function drawGrid() {
  ctx.save();
  ctx.strokeStyle = "rgba(0,240,255,0.045)";
  ctx.lineWidth = 1;
  const step = 48;
  for (let x = 0; x < W; x += step) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += step) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.restore();
}

function drawCrosshair(x, y) {
  const yy = y + S.recoil;
  ctx.save();
  ctx.translate(x, yy);
  const arms = [[0, -15, 0, -7], [0, 15, 0, 7], [-15, 0, -7, 0], [15, 0, 7, 0]];
  function stroke(color, w) {
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.lineCap = "square";
    ctx.beginPath();
    for (const a of arms) { ctx.moveTo(a[0], a[1]); ctx.lineTo(a[2], a[3]); }
    ctx.moveTo(-5, -11); ctx.lineTo(0, -15); ctx.lineTo(5, -11);
    ctx.moveTo(-5, 11); ctx.lineTo(0, 15); ctx.lineTo(5, 11);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(0, 0, 1.6, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }
  stroke("rgba(0,0,0,0.85)", 4.2);
  stroke("#f4fbff", 1.6);
  if (S.flash > 0) {
    const a = S.flash / 0.04;
    ctx.beginPath();
    ctx.arc(0, 0, 10 + (1 - a) * 8, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255,240,200," + (0.7 * a) + ")";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = "rgba(255,220,160," + (0.22 * a) + ")";
    ctx.beginPath();
    ctx.arc(0, 0, 6, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}
function drawOrb(o, now) {
  const t = (now - o.born) / 1000;
  const pop = Math.min(1, t / 0.12);
  const r = o.r * (0.2 + 0.8 * pop);
  const pulse = 1 + Math.sin(now * 0.007 + o.x) * 0.04;
  const rr = r * pulse;
  const core = "hsla(" + o.hue + ",100%,62%,1)";
  const glow = ctx.createRadialGradient(o.x, o.y, 1, o.x, o.y, rr * 2.1);
  glow.addColorStop(0, "hsla(" + o.hue + ",100%,70%,0.55)");
  glow.addColorStop(0.35, "hsla(" + o.hue + ",100%,50%,0.18)");
  glow.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(o.x, o.y, rr * 2.1, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.arc(o.x, o.y, rr, 0, Math.PI * 2);
  ctx.fillStyle = "hsla(" + o.hue + ",95%,18%,0.92)";
  ctx.fill();
  ctx.strokeStyle = core;
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(o.x - rr * 0.18, o.y - rr * 0.2, rr * 0.38, 0, Math.PI * 2);
  ctx.fillStyle = "hsla(" + o.hue + ",100%,78%,0.95)";
  ctx.fill();
}

function drawModeChip() {
  const label = S.seeking && S.mode !== "DESKTOP" && !S.desktop ? "SEEKING" : S.mode;
  const col = label === "GUN" ? "#00f0ff" : label === "DESKTOP" ? "#ffd56a" : label === "SEEKING" ? "#ff2bd6" : "#6a7a88";
  ctx.save();
  ctx.font = "700 11px system-ui, sans-serif";
  ctx.letterSpacing = "0.18em";
  const tw = ctx.measureText(label).width + 22;
  ctx.fillStyle = "rgba(5,8,14,0.72)";
  ctx.strokeStyle = col;
  ctx.lineWidth = 1;
  ctx.fillRect(16, 16, tw, 22);
  ctx.strokeRect(16, 16, tw, 22);
  ctx.fillStyle = col;
  ctx.textBaseline = "middle";
  ctx.fillText(label, 27, 28);
  const q = clamp(Math.round(S.quality), 0, 100);
  const qLabel = "CONF " + q;
  ctx.letterSpacing = "0.12em";
  const qw = ctx.measureText(qLabel).width + 22;
  const qx = 16 + tw + 8;
  const qCol = q >= 70 ? "#00f0ff" : q >= 40 ? "#ffd56a" : "#ff2bd6";
  ctx.fillStyle = "rgba(5,8,14,0.72)";
  ctx.strokeStyle = qCol;
  ctx.fillRect(qx, 16, qw, 22);
  ctx.strokeRect(qx, 16, qw, 22);
  ctx.fillStyle = qCol;
  ctx.fillText(qLabel, qx + 11, 26);
  ctx.letterSpacing = "0";
  ctx.fillStyle = "rgba(255,255,255,0.12)";
  ctx.fillRect(qx + 4, 35, qw - 8, 3);
  ctx.fillStyle = qCol;
  ctx.fillRect(qx + 4, 35, (qw - 8) * (q / 100), 3);
  ctx.restore();
}
function drawHUD(now) {
  drawModeChip();
  if (phase !== "range") return;
  const left = Math.max(0, RANGE_MS - (now - S.rangeStart));
  const sec = (left / 1000).toFixed(1);
  ctx.save();
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.fillStyle = "#f4fbff";
  ctx.font = "900 34px Impact, 'Arial Narrow', system-ui, sans-serif";
  ctx.fillText(String(S.score), W / 2, 16);
  ctx.font = "700 12px system-ui, sans-serif";
  ctx.fillStyle = "#00f0ff";
  ctx.fillText("SCORE", W / 2, 52);
  ctx.fillStyle = "#ff2bd6";
  ctx.font = "900 22px Impact, 'Arial Narrow', system-ui, sans-serif";
  if (S.combo > 1) ctx.fillText(S.combo + "x", W / 2, 70);
  ctx.fillStyle = "#e8f6ff";
  ctx.font = "700 18px Impact, 'Arial Narrow', system-ui, sans-serif";
  ctx.textAlign = "right";
  ctx.fillText(sec, W - HUD_PAD, 16);
  ctx.font = "700 10px system-ui, sans-serif";
  ctx.fillStyle = "#00f0ff";
  ctx.fillText("TIME", W - HUD_PAD, 38);
  ctx.restore();
  if (S.mode === "PAD") {
    S.liftPulse += 0.05;
    ctx.save();
    ctx.globalAlpha = 0.45 + Math.sin(S.liftPulse) * 0.2;
    ctx.textAlign = "center";
    ctx.font = "700 22px Impact, 'Arial Narrow', system-ui, sans-serif";
    ctx.fillStyle = "#00f0ff";
    ctx.letterSpacing = "0.2em";
    ctx.fillText("LIFT THE MOUSE", W / 2, H * 0.78);
    ctx.restore();
  }
}

function drawCalib(now) {
  const corners = screenCorners();
  for (let i = 0; i < 4; i++) {
    const c = corners[i];
    const got = !!S.camPts[i];
    const active = i === S.calibIndex && S.calibIndex < 4;
    ctx.beginPath();
    ctx.arc(c.x, c.y, active ? 22 : 10, 0, Math.PI * 2);
    ctx.strokeStyle = got ? "#00f0ff" : active ? "#ff2bd6" : "rgba(255,255,255,0.2)";
    ctx.lineWidth = active ? 2.5 : 1.5;
    ctx.stroke();
    if (active) {
      const pulse = 16 + Math.sin(now * 0.008) * 8;
      ctx.beginPath();
      ctx.arc(c.x, c.y, 34 + pulse, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255,43,214," + (0.35 + Math.sin(now * 0.01) * 0.2) + ")";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "rgba(255,43,214,0.18)";
      ctx.beginPath();
      ctx.arc(c.x, c.y, 14, 0, Math.PI * 2);
      ctx.fill();
    }
    if (got) {
      ctx.fillStyle = "#00f0ff";
      ctx.beginPath();
      ctx.arc(c.x, c.y, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  if (S.calibIndex >= 4) {
    drawOrb({ x: W / 2, y: H / 2, r: 38, hue: 185, born: now - 200, first: true }, now);
  }
  if (S.noLockFlash > 0) {
    ctx.save();
    ctx.globalAlpha = Math.min(1, S.noLockFlash * 2);
    ctx.fillStyle = "#ff2bd6";
    ctx.font = "700 16px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("NO LOCK", W / 2, H * 0.18);
    ctx.restore();
  }
}
function draw() {
  const now = performance.now();
  ctx.save();
  if (S.punch > 0.05) {
    const a = Math.random() * Math.PI * 2;
    ctx.translate(Math.cos(a) * S.punch, Math.sin(a) * S.punch);
  }
  bg();
  drawGrid();
  if (phase === "lock") {
    drawModeChip();
  } else if (phase === "calibrate") {
    drawCalib(now);
    drawCrosshair(S.aim.x, S.aim.y);
    drawModeChip();
  } else if (phase === "range") {
    for (const o of S.orbs) drawOrb(o, now);
    for (const p of S.parts) {
      const a = 1 - p.age / p.life;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = "hsla(" + p.hue + ",100%,70%," + a + ")";
      ctx.fill();
    }
    for (const p of S.pops) {
      const a = 1 - p.age / p.life;
      ctx.globalAlpha = a;
      ctx.fillStyle = "hsla(" + p.hue + ",100%,70%,1)";
      ctx.font = "700 16px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(p.text, p.x, p.y);
      ctx.globalAlpha = 1;
    }
    drawCrosshair(S.aim.x, S.aim.y);
    drawHUD(now);
  }
  ctx.restore();
}

function frame(t) {
  requestAnimationFrame(frame);
  const dt = Math.min(0.05, lastT ? (t - lastT) / 1000 : 0.016);
  lastT = t;
  if (camReady) {
    if (grabFrame()) runTrack(t);
    else coastTrack(t);
    updateMode(t);
    updateAim();
  }
  if (phase === "lock") tickLock(t);
  if (S.hitstop > 0) { S.hitstop--; draw(); return; }
  S.recoil += (0 - S.recoil) * Math.min(1, dt * 18);
  S.punch *= Math.max(0, 1 - dt * 14);
  S.flash = Math.max(0, S.flash - dt);
  S.noLockFlash = Math.max(0, S.noLockFlash - dt);
  S.calibFlash = Math.max(0, S.calibFlash - dt);
  if (phase === "range") updateRange(dt, t);
  syncCursor();
  draw();
}
canvas.addEventListener("pointerdown", (e) => {
  if (e.button !== 0) return;
  unlockAudio();
  if (phase === "lock") {
    e.preventDefault();
    if (S.tpl && (detGood() || S.smooth)) goCalib();
    return;
  }
  if (phase === "calibrate") {
    e.preventDefault();
    const corners = screenCorners();
    let recap = -1;
    for (let i = 0; i < 4; i++) {
      if (S.camPts[i] && Math.hypot(e.clientX - corners[i].x, e.clientY - corners[i].y) < 40) recap = i;
    }
    if (recap >= 0) { S.calibIndex = recap; captureCorner(); }
    else if (S.calibIndex < 4) captureCorner();
    else fire();
    return;
  }
  if (phase === "range") { e.preventDefault(); fire(); }
});

window.addEventListener("contextmenu", (e) => e.preventDefault());

window.addEventListener("pointermove", (e) => {
  S.hidLast = performance.now();
  if (S.desktop) publishAim(e.clientX, e.clientY);
});

window.addEventListener("keydown", (e) => {
  if (e.code === "Space") { e.preventDefault(); S.forceGun = true; }
  if (e.code === "KeyT") {
    if (phase === "lock") { goDesktopRange(); return; }
    S.desktop = !S.desktop;
    if (S.desktop) S.mode = "DESKTOP";
  }
});

window.addEventListener("keyup", (e) => {
  if (e.code === "Space") S.forceGun = false;
});

window.addEventListener("resize", fit);

$("btn-play").addEventListener("click", () => { play(); });
$("btn-redo").addEventListener("click", () => {
  let last = -1;
  for (let i = 0; i < 4; i++) if (S.camPts[i]) last = i;
  if (last >= 0) {
    S.camPts[last] = null;
    S.H = null;
    S.calibIndex = last;
    updateCalibMsg();
  }
});
$("btn-again").addEventListener("click", () => setPhase("range"));
$("btn-recal").addEventListener("click", () => {
  S.camPts = [null, null, null, null];
  S.H = null;
  S.desktop = false;
  S.lockAdvance = false;
  setPhase("calibrate");
});

function syncCursor() {
  const hide = phase === "range" || phase === "calibrate" || phase === "lock";
  canvas.classList.toggle("nocursor", hide);
  const v = hide ? "none" : "";
  document.body.style.cursor = v;
  document.documentElement.style.cursor = v;
}

fit();
S.aim.x = W / 2;
S.aim.y = H / 2;
requestAnimationFrame(frame);
