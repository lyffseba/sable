/* SABLE — WebGL Physical-Aim Arena FPS
   Powered by Gemini 3.8 Flash Spatial Vision & Three.js 3D Engine.
   Inverted Light-Gun Geometry: webcam on monitor top, player points mouse nose at screen.
   HID left-click fires atomically from the AimBus mailbox. Physical ADS verb. */

import * as THREE from "./vendor/three.module.js";

const $ = (id) => document.getElementById(id);
const cam = $("cam");
const proc = $("proc");
const canvas3D = $("game");
const canvasHUD = $("hud");
const ctx = canvasHUD.getContext("2d");
const pctx = proc.getContext("2d", { willReadFrequently: true, alpha: false });

const screens = {
  boot: $("screen-boot"),
  lobby: $("screen-lobby"),
  lock: $("screen-lock"),
  calibrate: $("screen-calib"),
  range: $("screen-range"),
  results: $("screen-results"),
};

// --- Aim Protocol & Mailbox Contract ---
class AimSample {
  constructor(uv = { x: 0.5, y: 0.5 }, valid = false, lifted = false, confidence = 0.0, t_hw = 0) {
    this.uv = uv;
    this.valid = valid;
    this.lifted = lifted;
    this.confidence = confidence;
    this.t_hw = t_hw;
  }
}

class AimBus {
  constructor() {
    this._latest = new AimSample();
  }
  publish(sample) {
    this._latest = sample;
  }
  peek() {
    return this._latest;
  }
  fire() {
    return this._latest;
  }
}
const aimBus = new AimBus();

// --- Operator Identity & Locker Catalog ---
const OP_CANCHO = "cancho";
const STYLE_DEFAULT = "default";
const STYLE_RANKED = "ranked";
const STYLE_NIGHT = "night";

const Locker = {
  operator: {
    id: OP_CANCHO,
    displayName: "CANCHO",
    styles: [STYLE_DEFAULT, STYLE_RANKED, STYLE_NIGHT],
    vo: {
      lift: "¡Al aire!",
      hit: "¡Claro!",
      drop: "¡Al suelo!",
      win: "¡Se escribió!"
    }
  },
  equippedStyle: STYLE_DEFAULT,
  colors: {
    mint: "#59F2C7",
    mintHex: 0x59F2C7,
    bone: "#E6E0D1",
    boneHex: 0xE6E0D1,
    rust: "#8C472E",
    rustHex: 0x8C472E,
    bodyHex: 0x141a22,
  },
  cycleStyle() {
    const s = this.operator.styles;
    const idx = (s.indexOf(this.equippedStyle) + 1) % s.length;
    this.equippedStyle = s[idx];
    speak("Estilo: " + this.equippedStyle);
    return this.equippedStyle;
  }
};

// --- Tracking Constants & Parameters ---
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
const EURO_MINCUTOFF = 3.0, EURO_BETA = 0.03, EURO_DCUTOFF = 1.0;
const LIFT_ON_MS = 50;

let W = 1280, H = 720, dpr = 1, PROC_H = 270, phase = "boot";
let stream = null, camReady = false, lastT = 0;
let targetGameMode = "range";
let geminiLockPending = false;
let geminiAutoTried = false;

const S = {
  det: null, smooth: null, vel: { x: 0, y: 0 }, lastDetAt: 0, trackT: 0,
  camStamp: -1, quality: 0, euroX: null, euroY: null, lastRaw: null, seeking: false,
  H: null, useBilinear: false, camPts: [null, null, null, null], calibIndex: 0,
  calibFlash: 0, forceGun: false, desktop: false, hidLast: 0, hidMoving: false,
  mode: "PAD", lifted: false, liftMs: 0, liftTick: 0, aim: { x: 0.5, y: 0.5 },
  recoil: 0, punch: 0, flash: 0, hitstop: 0,
  orbs: [], parts: [], pops: [], score: 0, hits: 0, shots: 0, combo: 0, comboMax: 0,
  rangeStart: 0, lockSince: 0, locked: false, lockStart: 0, lockAdvance: false,
  noLockFlash: 0, liftPulse: 0, enteringRange: false,
  tpl: null, ncc: 0, gray: null,
  lockAcc: null, lockAccCols: 0, lockAccRows: 0,
  lockBestScore: 0, lockBestPatch: null, lockBestTL: null, lockTplAt: 0,
  engine: { mojo: null, gemini: false },
  online: false,
  playlist: "range",
  room: "",
  player: "",
  slot: -1,
  host: false,
};

// --- Bay 1v1 Arena State ---
const Bay = {
  active: false,
  you: 0,
  them: 0,
  toWin: 5,
  round: 1,
  speed: 5.2,
  pos: { x: 0, y: 1.64, z: 10 },
  foe: { x: 0, y: 0.89, z: -10, radius: 0.54, alive: true, strafeDir: 1, strafeT: 0 },
  frozen: false,
  freezeT: 0,
  freezePadS: 0.45,
  expose: 0,
  exposeMax: 0.14,
  voText: "",
  voT: 0,
  missT: 0,
  over: false,
  wasLifted: false,
  keys: { w: false, a: false, s: false, d: false },
  resetRound() {
    this.pos.x = 0; this.pos.y = 1.64; this.pos.z = 10;
    this.foe.x = (Math.random() - 0.5) * 4.2;
    this.foe.y = 0.89;
    this.foe.z = -10 - Math.random() * 2.0;
    this.foe.alive = true;
    this.foe.strafeDir = Math.random() < 0.5 ? 1 : -1;
    this.foe.strafeT = 0;
    this.expose = 0;
    this.frozen = false;
  },
  resetMatch() {
    this.you = 0;
    this.them = 0;
    this.round = 1;
    this.over = false;
    this.resetRound();
  },
  vo(line) {
    this.voText = line;
    this.voT = 0.9;
    speak(line);
  }
};

// --- Speech Synthesis Helper ---
function speak(text) {
  if (!window.speechSynthesis) return;
  try {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "es-ES";
    u.rate = 1.12;
    u.pitch = 0.88;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  } catch (e) {
    // Audio synthesis fallback
  }
}

// --- Math & Filtering ---
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

// --- Homography Solver (DLT) ---
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
    const sx = src[i].x, sy = src[i].y;
    const dx = dst[i].x, dy = dst[i].y;
    A.push([sx, sy, 1, 0, 0, 0, -dx * sx, -dx * sy]);
    b.push(dx);
    A.push([0, 0, 0, sx, sy, 1, -dy * sx, -dy * sy]);
    b.push(dy);
  }
  const h = solveLinear(A, b);
  if (!h) return null;
  return [h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], 1];
}

function screenCorners() {
  const m = 32;
  return [
    { x: m, y: m },
    { x: W - m, y: m },
    { x: W - m, y: H - m },
    { x: m, y: H - m },
  ];
}

function computeH() {
  if (!S.camPts.every(Boolean)) return;
  const dst = screenCorners();
  S.H = dltHomography(S.camPts, dst);
}

function camToScreen(cx, cy) {
  if (S.H) {
    const H = S.H;
    const z = H[6] * cx + H[7] * cy + H[8];
    if (Math.abs(z) > 1e-6) {
      const u = (H[0] * cx + H[1] * cy + H[2]) / z;
      const v = (H[3] * cx + H[4] * cy + H[5]) / z;
      return { x: clamp(u, 0, W), y: clamp(v, 0, H), lost: false };
    }
  }
  return { x: (cx / PROC_W) * W, y: (cy / PROC_H) * H, lost: false };
}

// --- Computer Vision & Template Matching ---
function predictedCam(now) {
  if (!S.smooth) return null;
  const dt = Math.max(0, (now - (S.trackT || now)) * 0.001);
  return { x: S.smooth.x + S.vel.x * dt, y: S.smooth.y + S.vel.y * dt };
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

function detGood() { return S.det && S.det.conf >= NCC_GOOD; }

function runTrack(now) {
  if (!S.euroX) resetTrackFilters();
  const stamp = cam.currentTime;
  if (stamp && stamp === S.camStamp) {
    if (!S.det) coastTrack(now);
    updateQuality(now, S.det);
    return;
  }
  S.camStamp = stamp;
  if (S.tpl) {
    nccTrack(now);
  } else {
    const img = pctx.getImageData(0, 0, PROC_W, PROC_H);
    sampleLock(img, now);
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
}

function grabFrame() {
  if (!camReady || !cam.videoWidth) return false;
  if (proc.width !== PROC_W) sizeProc();
  pctx.drawImage(cam, 0, 0, PROC_W, PROC_H);
  const img = pctx.getImageData(0, 0, PROC_W, PROC_H);
  const d = img.data;
  const gray = S.gray;
  for (let i = 0, j = 0; i < d.length; i += 4, j++) {
    gray[j] = (d[i] * 77 + d[i + 1] * 150 + d[i + 2] * 29) >> 8;
  }
  return true;
}

// --- Mode & Aim Mailbox Wiring ---
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
  if (aimBus.peek()) {
    aimBus.peek().lifted = S.lifted;
  }
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
  const nowUs = Math.round(performance.now() * 1000);
  const sample = new AimSample(
    { x: clamp(x / W, 0, 1), y: clamp(y / H, 0, 1) },
    !S.seeking && (S.locked || S.desktop),
    S.lifted,
    clamp(S.quality / 100, 0, 1),
    nowUs
  );
  aimBus.publish(sample);
}

function updateAim() {
  if (S.desktop) return;
  if (!S.smooth) return;
  if (phase !== "range" && phase !== "calibrate" && phase !== "bay") return;
  if (S.H || S.camPts.every(Boolean)) {
    const p = camToScreen(S.smooth.x, S.smooth.y);
    if (!p.lost) publishAim(p.x, p.y);
    else S.seeking = true;
  } else {
    publishAim((S.smooth.x / PROC_W) * W, (S.smooth.y / PROC_H) * H);
  }
}

// --- Gemini 3.8 Flash Spatial Vision Lock ---
async function requestGeminiLock() {
  if (geminiLockPending || phase !== "lock" || !camReady || !S.gray) return false;
  const st = $("lock-status");
  geminiLockPending = true;
  if (st) st.textContent = "GEMINI 3.8 ANALYZING...";

  try {
    const snap = proc.toDataURL("image/jpeg", 0.85);
    const resp = await fetch("/api/gemini/lock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: snap })
    });
    if (!resp.ok) throw new Error("API " + resp.status);
    const data = await resp.json();
    if (data.detected && data.muzzle_point && phase === "lock") {
      const mx = clamp((data.muzzle_point[1] / 1000) * PROC_W, 0, PROC_W - 1);
      const my = clamp((data.muzzle_point[0] / 1000) * PROC_H, 0, PROC_H - 1);
      const now = performance.now();
      commitTpl(S.gray, PROC_W, PROC_H, Math.round(mx - TPL * 0.5), Math.round(my - TPL * 0.5), now);
      S.quality = clamp((data.confidence || 0.95) * 100, 0, 100);
      S.locked = true;
      if (st) st.textContent = "AI LOCKED: " + (data.label || "MOUSE").toUpperCase();
      hitBlip(2);
      speak(data.label ? "Fijado: " + data.label : "Fijado.");
      setTimeout(() => { if (phase === "lock") goCalib(); }, 500);
      geminiLockPending = false;
      return true;
    }
  } catch (err) {
    console.warn("Gemini Muzzle Lock fallback:", err);
  }
  geminiLockPending = false;
  if (st && phase === "lock" && !S.locked) st.textContent = "SEEKING";
  return false;
}

// --- Audio Synthesizer ---
let actx = null;
function unlockAudio() {
  if (!actx) actx = new (window.AudioContext || window.webkitAudioContext)();
  if (actx.state === "suspended") actx.resume();
}

function bang() {
  if (!actx) return;
  const t = actx.currentTime;
  const osc = actx.createOscillator();
  const gain = actx.createGain();
  osc.type = "sawtooth";
  osc.frequency.setValueAtTime(320, t);
  osc.frequency.exponentialRampToValueAtTime(40, t + 0.12);
  gain.gain.setValueAtTime(0.42, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + 0.14);
  osc.connect(gain);
  gain.connect(actx.destination);
  osc.start(t);
  osc.stop(t + 0.15);
}

function hitBlip(combo) {
  if (!actx) return;
  const t = actx.currentTime;
  const osc = actx.createOscillator();
  const gain = actx.createGain();
  const baseFreq = 540 + Math.min(600, combo * 70);
  osc.type = "sine";
  osc.frequency.setValueAtTime(baseFreq, t);
  osc.frequency.exponentialRampToValueAtTime(baseFreq * 1.5, t + 0.08);
  gain.gain.setValueAtTime(0.3, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + 0.1);
  osc.connect(gain);
  gain.connect(actx.destination);
  osc.start(t);
  osc.stop(t + 0.11);
}

function missTick() {
  if (!actx) return;
  const t = actx.currentTime;
  const osc = actx.createOscillator();
  const gain = actx.createGain();
  osc.type = "triangle";
  osc.frequency.setValueAtTime(140, t);
  gain.gain.setValueAtTime(0.18, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + 0.035);
  osc.connect(gain);
  gain.connect(actx.destination);
  osc.start(t);
  osc.stop(t + 0.04);
}

// ==========================================
// --- Three.js 3D Engine Architecture ---
// ==========================================
let renderer, scene, camera;
let gunGroup, gunBody, gunStripe, gunMuzzleLight;
let rangeTargetGroup, rangeHallGroup, shardGroup;
let bayGroup, foeGroup, foeMesh, foeVisor;
let tracerLines = [];

function init3D() {
  renderer = new THREE.WebGLRenderer({
    canvas: canvas3D,
    antialias: true,
    powerPreference: "high-performance",
  });
  renderer.setSize(W, H);
  renderer.setPixelRatio(dpr);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.08;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x03050a);
  scene.fog = new THREE.FogExp2(0x03050a, 0.032);

  camera = new THREE.PerspectiveCamera(68, W / H, 0.08, 160);
  camera.position.set(0, 1.64, 0);

  scene.add(new THREE.HemisphereLight(0x4a6a88, 0x08060a, 0.85));
  const dir = new THREE.DirectionalLight(0xc8e8ff, 1.35);
  dir.position.set(4, 14, 7);
  scene.add(dir);
  const rim = new THREE.DirectionalLight(Locker.colors.mintHex, 0.35);
  rim.position.set(-8, 6, -4);
  scene.add(rim);

  buildFirstPersonGun();
  buildRange3D();
  buildBay3D();
}

function buildFirstPersonGun() {
  gunGroup = new THREE.Group();

  // Cybernetic Mouse-Gun body
  const bodyGeo = new THREE.BoxGeometry(0.08, 0.06, 0.22);
  const bodyMat = new THREE.MeshStandardMaterial({
    color: 0x11161d,
    roughness: 0.35,
    metalness: 0.8,
  });
  gunBody = new THREE.Mesh(bodyGeo, bodyMat);
  gunGroup.add(gunBody);

  // Mint Capacitor Stripe
  const stripeGeo = new THREE.BoxGeometry(0.084, 0.012, 0.16);
  const stripeMat = new THREE.MeshBasicMaterial({ color: Locker.colors.mintHex });
  gunStripe = new THREE.Mesh(stripeGeo, stripeMat);
  gunStripe.position.set(0, 0.026, 0.01);
  gunGroup.add(gunStripe);

  // Rust Wrist Accent
  const rustGeo = new THREE.BoxGeometry(0.082, 0.04, 0.04);
  const rustMat = new THREE.MeshStandardMaterial({
    color: Locker.colors.rustHex,
    roughness: 0.6,
  });
  const rustMesh = new THREE.Mesh(rustGeo, rustMat);
  rustMesh.position.set(0, -0.01, 0.1);
  gunGroup.add(rustMesh);

  const barrel = new THREE.Mesh(
    new THREE.CylinderGeometry(0.012, 0.014, 0.16, 10),
    new THREE.MeshStandardMaterial({ color: 0x1a222c, metalness: 0.9, roughness: 0.2 })
  );
  barrel.rotation.x = Math.PI / 2;
  barrel.position.set(0, 0.008, -0.16);
  gunGroup.add(barrel);

  gunMuzzleLight = new THREE.PointLight(Locker.colors.mintHex, 0, 5);
  gunMuzzleLight.position.set(0, 0.008, -0.24);
  gunGroup.add(gunMuzzleLight);

  // Default rest pose (lowered on pad)
  gunGroup.position.set(0.24, -0.22, -0.42);
  camera.add(gunGroup);
  scene.add(camera);
}

function buildRange3D() {
  rangeHallGroup = new THREE.Group();
  rangeTargetGroup = new THREE.Group();
  shardGroup = new THREE.Group();
  scene.add(rangeHallGroup);
  scene.add(rangeTargetGroup);
  scene.add(shardGroup);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(28, 28),
    new THREE.MeshStandardMaterial({ color: 0x07090e, roughness: 0.92, metalness: 0.12 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -1.64;
  rangeHallGroup.add(floor);
  const hallGrid = new THREE.GridHelper(28, 28, 0x0a3a44, 0x0a1820);
  hallGrid.position.y = -1.63;
  rangeHallGroup.add(hallGrid);

  const wallMat = new THREE.MeshStandardMaterial({ color: 0x0a1018, roughness: 0.88 });
  const back = new THREE.Mesh(new THREE.BoxGeometry(28, 10, 0.4), wallMat);
  back.position.set(0, 3.2, -14);
  rangeHallGroup.add(back);
  const strip = new THREE.Mesh(
    new THREE.BoxGeometry(18, 0.08, 0.12),
    new THREE.MeshBasicMaterial({ color: Locker.colors.mintHex })
  );
  strip.position.set(0, 6.4, -13.7);
  rangeHallGroup.add(strip);
}

function buildBay3D() {
  bayGroup = new THREE.Group();
  bayGroup.visible = false;
  scene.add(bayGroup);

  // Arena Floor Grid
  const grid = new THREE.GridHelper(40, 20, 0x00f0ff, 0x113344);
  grid.position.y = 0;
  bayGroup.add(grid);

  // Floor plane
  const floorGeo = new THREE.PlaneGeometry(40, 40);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x03060a,
    roughness: 0.9,
    metalness: 0.2,
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  bayGroup.add(floor);

  // Concrete Pillars & Barriers
  const pillarGeo = new THREE.BoxGeometry(2.4, 8, 2.4);
  const pillarMat = new THREE.MeshStandardMaterial({ color: 0x09121c, roughness: 0.8 });
  for (const [x, z] of [[-6, -4], [6, -4], [0, -16], [-10, 2], [10, 2]]) {
    const p = new THREE.Mesh(pillarGeo, pillarMat);
    p.position.set(x, 4, z);
    bayGroup.add(p);
  }
  const neon = new THREE.MeshBasicMaterial({ color: Locker.colors.mintHex });
  for (const z of [-8, 0, 8]) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(22, 0.06, 0.1), neon);
    bar.position.set(0, 7.2, z);
    bayGroup.add(bar);
  }

  // Left Window Cover
  const coverGeo = new THREE.BoxGeometry(3.2, 2.4, 0.8);
  const coverMat = new THREE.MeshStandardMaterial({ color: 0x0c1824, roughness: 0.6 });
  const leftCover = new THREE.Mesh(coverGeo, coverMat);
  leftCover.position.set(-5.5, 1.2, 4.0);
  const rightCover = new THREE.Mesh(coverGeo, coverMat);
  rightCover.position.set(5.5, 1.2, 3.5);
  bayGroup.add(leftCover);
  bayGroup.add(rightCover);

  // Foe CANCHO Opponent Capsule
  foeGroup = new THREE.Group();
  const foeBodyGeo = new THREE.CapsuleGeometry(0.48, 1.1, 8, 16);
  const foeBodyMat = new THREE.MeshStandardMaterial({ color: 0x141a22, roughness: 0.4 });
  foeMesh = new THREE.Mesh(foeBodyGeo, foeBodyMat);
  foeMesh.position.y = 1.0;
  foeGroup.add(foeMesh);

  // Mint Visor
  const visorGeo = new THREE.BoxGeometry(0.52, 0.12, 0.32);
  const visorMat = new THREE.MeshBasicMaterial({ color: Locker.colors.mintHex });
  foeVisor = new THREE.Mesh(visorGeo, visorMat);
  foeVisor.position.set(0, 1.35, 0.25);
  foeGroup.add(foeVisor);
  const visorLight = new THREE.PointLight(Locker.colors.mintHex, 1.4, 6);
  visorLight.position.set(0, 1.42, 0.4);
  foeGroup.add(visorLight);

  foeGroup.position.set(0, 0, -10);
  bayGroup.add(foeGroup);
}

// --- 3D Target Spawn & Shatter ---
function createTargetMesh(kind, hue) {
  const group = new THREE.Group();
  const geo = kind === "sine"
    ? new THREE.OctahedronGeometry(0.55, 1)
    : new THREE.IcosahedronGeometry(0.52, 0);

  const col = new THREE.Color(`hsl(${hue}, 100%, 65%)`);
  const coreMat = new THREE.MeshStandardMaterial({
    color: col,
    emissive: col,
    emissiveIntensity: 0.65,
    roughness: 0.2,
  });
  const core = new THREE.Mesh(geo, coreMat);
  group.add(core);

  const wireMat = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true });
  const wire = new THREE.Mesh(geo, wireMat);
  wire.scale.setScalar(1.12);
  group.add(wire);

  return { group, core, wire };
}

function spawnOrb3D(opts) {
  const o = Object.assign({
    x: 0, y: 0, r: 24, kind: "static", vx: 0, vy: 0,
    amp: 0, freq: 0, baseY: 0, phase: 0, worth: 100, hue: 185,
    life: 0, born: performance.now(),
  }, opts);

  const meshObj = createTargetMesh(o.kind, o.hue);
  o.mesh = meshObj.group;
  rangeTargetGroup.add(o.mesh);

  // Position target in 3D camera frustum space at depth z = -5.0
  const normX = (o.x / W) * 2 - 1;
  const normY = -(o.y / H) * 2 + 1;
  const depth = 5.2;
  const v = new THREE.Vector3(normX, normY, 0.5).unproject(camera);
  const dir = v.sub(camera.position).normalize();
  const dist = depth / -dir.z;
  o.mesh.position.copy(camera.position).add(dir.multiplyScalar(dist));

  S.orbs.push(o);
  return o;
}

function shatterTarget3D(pos, hue) {
  const count = 16;
  const col = new THREE.Color(`hsl(${hue}, 100%, 65%)`);
  const shardMat = new THREE.MeshBasicMaterial({ color: col });
  for (let i = 0; i < count; i++) {
    const sGeo = new THREE.TetrahedronGeometry(0.08 + Math.random() * 0.08);
    const m = new THREE.Mesh(sGeo, shardMat);
    m.position.copy(pos);
    const vel = new THREE.Vector3(
      (Math.random() - 0.5) * 6,
      (Math.random() - 0.5) * 6 + 1.5,
      (Math.random() - 0.5) * 6
    );
    shardGroup.add(m);
    S.parts.push({ mesh: m, vel, life: 0.6, age: 0 });
  }
}

function addBulletTracer(from, to) {
  const geo = new THREE.BufferGeometry().setFromPoints([from, to]);
  const mat = new THREE.LineBasicMaterial({ color: Locker.colors.mintHex, linewidth: 2 });
  const line = new THREE.Line(geo, mat);
  scene.add(line);
  tracerLines.push({ line, age: 0, life: 0.065 });
}

// --- HID Fire Contract & Hitscan ---
function fire() {
  if (phase !== "range" && phase !== "bay" && !(phase === "calibrate" && S.calibIndex >= 4)) return;
  if (!S.desktop && S.smooth) {
    const now = performance.now();
    if (now - (S.trackT || 0) > 0) coastTrack(now);
    updateAim();
  }
  // Peek the mailbox. Lift is the trigger. Camera already wrote S.aim.
  const shot = aimBus.fire();
  if (!S.desktop && !S.lifted) return;

  bang();
  S.recoil = 2.4; S.flash = 0.06; S.punch = 1.8;

  // Gun recoil animation & muzzle flash in 3D
  if (gunMuzzleLight) gunMuzzleLight.intensity = 3.5;
  if (gunGroup) {
    gunGroup.position.z += 0.07;
    gunGroup.rotation.x += 0.15;
  }

  // Hitscan raycast from camera through Aim reticle UV
  const mouseNorm = new THREE.Vector2((S.aim.x / W) * 2 - 1, -(S.aim.y / H) * 2 + 1);
  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera(mouseNorm, camera);

  const muzzleWorld = new THREE.Vector3();
  gunMuzzleLight.getWorldPosition(muzzleWorld);

  if (phase === "bay") {
    fireBay3D(raycaster, muzzleWorld);
    return;
  }

  if (phase === "calibrate") {
    S.shots++;
    const tx = W / 2, ty = H / 2;
    if (Math.hypot(S.aim.x - tx, S.aim.y - ty) < 48) {
      hitBlip(1); S.hitstop = 1;
      if (!S.enteringRange) {
        S.enteringRange = true;
        setTimeout(() => { S.enteringRange = false; enterGame(); }, 400);
      }
    } else missTick();
    return;
  }

  S.shots++;
  let hit = null;
  for (const o of S.orbs) {
    const dist = Math.hypot(S.aim.x - o.x, S.aim.y - o.y);
    if (dist < o.r + 14) { hit = o; break; }
  }

  if (hit) {
    S.combo++;
    if (S.combo > S.comboMax) S.comboMax = S.combo;
    const pts = hit.worth * S.combo;
    S.score += pts; S.hits++;
    hitBlip(S.combo); S.hitstop = 1;

    const hitPos = hit.mesh.position.clone();
    addBulletTracer(muzzleWorld, hitPos);
    shatterTarget3D(hitPos, hit.hue);
    popup(hit.x, hit.y - hit.r, (S.combo > 1 ? S.combo + "x " : "") + pts, hit.hue);

    rangeTargetGroup.remove(hit.mesh);
    S.orbs = S.orbs.filter((o) => o !== hit);
  } else {
    S.combo = 0;
    missTick();
    const farPoint = raycaster.ray.origin.clone().add(raycaster.ray.direction.clone().multiplyScalar(20));
    addBulletTracer(muzzleWorld, farPoint);
  }
}

function fireBay3D(raycaster, muzzleWorld) {
  if (Bay.frozen || Bay.over) { missTick(); return; }

  const intersects = raycaster.intersectObject(foeMesh, true);
  if (intersects.length > 0 && Bay.foe.alive) {
    const hitPt = intersects[0].point;
    addBulletTracer(muzzleWorld, hitPt);
    Bay.you++;
    Bay.foe.alive = false;
    foeGroup.visible = false;
    Bay.vo(Locker.operator.vo.hit);
    hitBlip(Bay.you);
    S.hitstop = 1;
    shatterTarget3D(hitPt, 160);

    if (Bay.you >= Bay.toWin) {
      Bay.over = true;
      Bay.frozen = true;
      Bay.vo(Locker.operator.vo.win);
    } else {
      Bay.frozen = true;
      Bay.freezeT = 0;
    }
  } else {
    missTick();
    Bay.missT = 0.06;
    const farPt = raycaster.ray.origin.clone().add(raycaster.ray.direction.clone().multiplyScalar(24));
    addBulletTracer(muzzleWorld, farPt);
  }
}

function enterGame() {
  setPhase("range");
}

function goDesktopRange() {
  if (S.lockAdvance) return;
  S.lockAdvance = true;
  S.desktop = true;
  S.mode = "DESKTOP";
  enterGame();
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
  geminiLockPending = false;
  geminiAutoTried = false;
  S.tpl = null; S.ncc = 0; S.det = null;
  S.lockAcc = null; S.lockBestScore = 0; S.lockBestPatch = null; S.lockBestTL = null;
  S.lockTplAt = 0; S.lockSince = 0; S.locked = false; S.lockAdvance = false;
  S.desktop = false; S.mode = "SEEKING"; S.smooth = null;
  S.lifted = false; S.liftMs = 0; S.liftTick = 0;
  resetTrackFilters();
}

let lobbyTimer = 0;
let lobbyStarting = false;

function stopLobbyPoll() {
  if (lobbyTimer) { clearInterval(lobbyTimer); lobbyTimer = 0; }
}

function paintLobby(data) {
  if (!data || !data.ok) return;
  S.room = data.code;
  S.host = data.host === S.player;
  S.playlist = "5v5";
  const room = $("lobby-room");
  if (room) room.textContent = "ROOM  " + data.code;
  const kicker = $("lobby-kicker");
  if (kicker) kicker.textContent = data.phase === "wait" ? "5v5  ·  WAITING ARENA" : "5v5  ·  RANGE";
  const tag = $("lobby-tag");
  if (tag) {
    tag.textContent = S.host
      ? "You host. ENTER RANGE starts the same ground for everyone in this room."
      : "Waiting on host. Same Range as offline when they start.";
  }
  const el = $("lobby-slots");
  if (el && data.slots) {
    const rows = ["<b>ALPHA</b><b>BRAVO</b>"];
    for (let i = 0; i < 5; i++) {
      const A = data.slots[i];
      const B = data.slots[i + 5];
      const an = A ? ((A.id === S.player ? "YOU  " : "") + A.name) : "—";
      const bn = B ? ((B.id === S.player ? "YOU  " : "") + B.name) : "—";
      rows.push(
        "<span class=\"" + (A && A.id === S.player ? "you" : "") + "\">" + (i + 1) + "  " + an + "</span>" +
        "<span class=\"" + (B && B.id === S.player ? "you" : "") + "\">" + (i + 6) + "  " + bn + "</span>"
      );
    }
    el.innerHTML = rows.join("");
  }
  const enter = $("btn-lobby-range");
  if (enter) enter.hidden = !S.host && data.phase === "wait";
}

async function lobbyCreate() {
  const res = await fetch("/api/lobby/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "HOST" }),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || "create failed");
  S.player = data.player;
  S.slot = data.slot;
  S.online = true;
  paintLobby(data);
  setPhase("lobby");
  stopLobbyPoll();
  lobbyTimer = setInterval(lobbyPoll, 400);
}

async function lobbyJoin(code) {
  if (S.room && S.player) {
    try {
      await fetch("/api/lobby/leave", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: S.room, player: S.player }),
      });
    } catch (e) { /* ignore */ }
  }
  const res = await fetch("/api/lobby/join", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: code, name: "PLAYER" }),
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || "join failed");
  S.player = data.player;
  S.slot = data.slot;
  S.online = true;
  paintLobby(data);
  setPhase("lobby");
  stopLobbyPoll();
  lobbyTimer = setInterval(lobbyPoll, 400);
}

async function lobbyPoll() {
  if (phase !== "lobby" || !S.room) return;
  try {
    const res = await fetch("/api/lobby?code=" + encodeURIComponent(S.room));
    const data = await res.json();
    if (!data.ok) return;
    paintLobby(data);
    if (data.phase === "range" && !lobbyStarting) {
      lobbyStarting = true;
      stopLobbyPoll();
      play("range");
    }
  } catch (e) { /* keep polling */ }
}

async function lobbyStartRange() {
  if (!S.room || !S.player) {
    play("range");
    return;
  }
  if (S.host) {
    await fetch("/api/lobby/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: S.room, player: S.player }),
    });
  }
  lobbyStarting = true;
  stopLobbyPoll();
  play("range");
}

async function lobbyLeave() {
  stopLobbyPoll();
  if (S.room && S.player) {
    try {
      await fetch("/api/lobby/leave", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: S.room, player: S.player }),
      });
    } catch (e) { /* ignore */ }
  }
  S.online = false;
  S.player = "";
  S.room = "";
  S.host = false;
  lobbyStarting = false;
  const playBtn = $("btn-play");
  if (playBtn) { playBtn.disabled = false; playBtn.textContent = "OFFLINE"; }
  const onBtn = $("btn-online");
  if (onBtn) onBtn.disabled = false;
  setPhase("boot");
}

async function openLobby() {
  try {
    await lobbyCreate();
  } catch (e) {
    S.online = true;
    setPhase("lobby");
  }
}

async function play(target = "range") {
  targetGameMode = "range";
  unlockAudio();
  const playBtn = $("btn-play");
  if (playBtn) {
    playBtn.disabled = true;
    playBtn.textContent = "...";
  }
  const onBtn = $("btn-online");
  if (onBtn) onBtn.disabled = true;
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
  if (rangeTargetGroup) rangeTargetGroup.visible = (next === "range");
  if (rangeHallGroup) rangeHallGroup.visible = (next !== "bay");
  if (bayGroup) bayGroup.visible = false;

  if (next === "calibrate") {
    S.calibIndex = S.camPts.every(Boolean) ? 4 : firstMissingCorner();
    updateCalibMsg();
    $("btn-redo").hidden = !S.camPts.some(Boolean) || S.calibIndex >= 4;
  }
  if (next === "range") startRange();
  if (next === "bay") {
    Bay.active = true;
    Bay.resetMatch();
    foeGroup.visible = true;
  }
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
  while (rangeTargetGroup && rangeTargetGroup.children.length > 0) {
    rangeTargetGroup.remove(rangeTargetGroup.children[0]);
  }
  S.orbs = []; S.parts = []; S.pops = [];
  S.score = 0; S.hits = 0; S.shots = 0; S.combo = 0; S.comboMax = 0;
  S.rangeStart = performance.now();
  S.recoil = 0; S.punch = 0; S.flash = 0;
  spawnOrb3D({ x: W / 2, y: H * 0.46, r: 38, kind: "static", worth: 100, hue: 180 });
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
    if (t - S.lockStart > 1800 && !geminiAutoTried && !geminiLockPending) {
      geminiAutoTried = true;
      requestGeminiLock();
    }
    if (st && !geminiLockPending) st.textContent = (t - S.lockStart < LOCK_SAMPLE_MS) ? "LOCKING" : "SEEKING";
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

function randomOrb(hard) {
  let x, y, r, guard = 0;
  const small = hard || Math.random() < 0.28;
  r = small ? 14 + Math.random() * 6 : 22 + Math.random() * 12;
  do {
    x = 90 + Math.random() * (W - 180);
    y = 90 + Math.random() * (H - 180);
    guard++;
  } while (nearOther(x, y, r + 40) && guard < 40);
  const roll = Math.random();
  let kind = "static";
  if (roll > 0.7) kind = "sine";
  else if (roll > 0.4) kind = "drift";
  const hue = small ? 320 : (Math.random() < 0.5 ? 185 : 160);
  const worth = small ? 250 : 100;
  return spawnOrb3D({
    x, y, r, kind, worth, hue,
    vx: kind === "drift" ? (Math.random() * 70 + 30) * (Math.random() < 0.5 ? -1 : 1) : 0,
    vy: kind === "drift" ? (Math.random() * 40 - 20) : 0,
    amp: kind === "sine" ? 18 + Math.random() * 26 : 0,
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

function popup(x, y, text, hue) {
  S.pops.push({ x, y, text, hue, age: 0, life: 0.7 });
}

function desiredOrbCount(elapsed) {
  if (elapsed < 2000) return 1;
  if (elapsed < 12000) return 3;
  if (elapsed < 28000) return 5;
  return 6;
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

    if (o.mesh) {
      const normX = (o.x / W) * 2 - 1;
      const normY = -(o.y / H) * 2 + 1;
      const depth = 5.2;
      const v = new THREE.Vector3(normX, normY, 0.5).unproject(camera);
      const dir = v.sub(camera.position).normalize();
      o.mesh.position.copy(camera.position).add(dir.multiplyScalar(depth / -dir.z));
      o.mesh.rotation.y += 1.4 * dt;
      o.mesh.rotation.x += 0.8 * dt;
    }
  }

  for (const p of S.pops) { p.age += dt; p.y -= 36 * dt; }
  S.pops = S.pops.filter((p) => p.age < p.life);
}

function tickBay(dt) {
  if (phase !== "bay") return;
  const sample = aimBus.peek();

  // VO on lift state transition
  if (!Bay.over) {
    if (sample.lifted && !Bay.wasLifted) {
      Bay.vo(Locker.operator.vo.lift);
    } else if (!sample.lifted && Bay.wasLifted) {
      Bay.vo(Locker.operator.vo.drop);
    }
  }
  Bay.wasLifted = sample.lifted;

  if (Bay.frozen && !Bay.over) {
    Bay.freezeT += dt;
    if (Bay.freezeT >= Bay.freezePadS && !sample.lifted) {
      Bay.round++;
      Bay.resetRound();
      foeGroup.visible = true;
    }
    return;
  }

  if (Bay.over) return;

  // WASD only on pad (PAD mode). Lift locks walk for physical ADS aiming!
  if (!sample.lifted) {
    let mx = 0, mz = 0;
    if (Bay.keys.w) mz -= 1;
    if (Bay.keys.s) mz += 1;
    if (Bay.keys.a) mx -= 1;
    if (Bay.keys.d) mx += 1;
    if (mx !== 0 && mz !== 0) { mx *= 0.7071; mz *= 0.7071; }
    Bay.pos.x = clamp(Bay.pos.x + mx * Bay.speed * dt, -7.0, 7.0);
    Bay.pos.z = clamp(Bay.pos.z + mz * Bay.speed * dt, 1.0, 14.0);
    camera.position.x = Bay.pos.x;
    camera.position.z = Bay.pos.z;
  }

  // Foe bot strafe AI
  if (Bay.foe.alive) {
    Bay.foe.strafeT += dt;
    if (Bay.foe.strafeT > 1.8) {
      Bay.foe.strafeT = 0;
      Bay.foe.strafeDir = Math.random() < 0.5 ? 1 : -1;
    }
    Bay.foe.x = clamp(Bay.foe.x + Bay.foe.strafeDir * 2.8 * dt, -4.5, 4.5);
    foeGroup.position.set(Bay.foe.x, Bay.foe.y, Bay.foe.z);
    foeGroup.lookAt(camera.position.x, foeGroup.position.y, camera.position.z);
  }

  // Open Middle Danger
  const inWindow = Bay.pos.x < -4.8;
  const inAngle = Bay.pos.x > 4.6;
  const inOpen = !inWindow && !inAngle && Bay.pos.z < 8.0;
  if (inOpen && !sample.lifted) {
    Bay.expose += dt;
    if (Bay.expose >= Bay.exposeMax) {
      Bay.them++;
      Bay.expose = 0;
      missTick();
      if (Bay.them >= Bay.toWin) {
        Bay.over = true;
        Bay.frozen = true;
        Bay.vo(Locker.operator.vo.win);
      } else {
        Bay.frozen = true;
        Bay.freezeT = 0;
      }
    }
  } else {
    Bay.expose = Math.max(0, Bay.expose - dt * 2.0);
  }

  if (Bay.voT > 0) Bay.voT = Math.max(0, Bay.voT - dt);
  if (Bay.missT > 0) Bay.missT = Math.max(0, Bay.missT - dt);
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

  canvas3D.width = Math.round(W * dpr);
  canvas3D.height = Math.round(H * dpr);
  canvasHUD.width = Math.round(W * dpr);
  canvasHUD.height = Math.round(H * dpr);

  canvas3D.style.width = W + "px";
  canvas3D.style.height = H + "px";
  canvasHUD.style.width = W + "px";
  canvasHUD.style.height = H + "px";

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  if (renderer && camera) {
    renderer.setSize(W, H);
    camera.aspect = W / H;
    camera.updateProjectionMatrix();
  }
  if (S.camPts.every(Boolean)) computeH();
}

// --- 2D HUD Rendering ---
function drawCrosshair(x, y) {
  const yy = y + S.recoil;
  ctx.save();
  ctx.translate(x, yy);
  const arms = [[0, -15, 0, -7], [0, 15, 0, 7], [-15, 0, -7, 0], [15, 0, 7, 0]];
  ctx.strokeStyle = Locker.colors.mint;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  for (const a of arms) { ctx.moveTo(a[0], a[1]); ctx.lineTo(a[2], a[3]); }
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(0, 0, 1.8, 0, Math.PI * 2);
  ctx.fillStyle = Locker.colors.mint;
  ctx.fill();
  ctx.restore();
}

function drawModeChip() {
  const label = S.seeking && S.mode !== "DESKTOP" && !S.desktop ? "SEEKING" : S.mode;
  const col = label === "GUN" ? "#00f0ff" : label === "DESKTOP" ? "#ffd56a" : label === "SEEKING" ? "#ff2bd6" : "#6a7a88";
  ctx.save();
  ctx.font = "700 11px system-ui, sans-serif";
  ctx.letterSpacing = "0.18em";
  const tw = ctx.measureText(label).width + 22;
  ctx.fillStyle = "rgba(5,8,14,0.78)";
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
  ctx.fillStyle = "rgba(5,8,14,0.78)";
  ctx.strokeStyle = qCol;
  ctx.fillRect(qx, 16, qw, 22);
  ctx.strokeRect(qx, 16, qw, 22);
  ctx.fillStyle = qCol;
  ctx.fillText(qLabel, qx + 11, 26);

  function chip(text, on, x) {
    const w = ctx.measureText(text).width + 18;
    ctx.fillStyle = "rgba(5,8,14,0.78)";
    ctx.strokeStyle = on ? Locker.colors.mint : "#3a4450";
    ctx.fillRect(x, 16, w, 22);
    ctx.strokeRect(x, 16, w, 22);
    ctx.fillStyle = on ? Locker.colors.mint : "#6a7a88";
    ctx.fillText(text, x + 9, 28);
    return w + 8;
  }
  let ex = W - 16;
  const mojoOn = !!S.engine.mojo;
  const gemOn = !!S.engine.gemini;
  const mLabel = mojoOn ? "MOJO 1.0" : "MOJO OFF";
  const gLabel = gemOn ? "GEMINI" : "GEMINI OFF";
  ex -= ctx.measureText(gLabel).width + 18;
  chip(gLabel, gemOn, ex);
  ex -= 8 + ctx.measureText(mLabel).width + 18;
  chip(mLabel, mojoOn, ex);
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
  ctx.font = "900 34px Impact, system-ui, sans-serif";
  ctx.fillText(String(S.score), W / 2, 16);
  ctx.font = "700 12px system-ui, sans-serif";
  ctx.fillStyle = "#00f0ff";
  const sess = !S.online ? "OFFLINE RANGE" : (S.playlist === "5v5" ? "5v5  " + S.room : "ONLINE RANGE");
  ctx.fillText("SCORE  ·  " + sess, W / 2, 52);
  if (S.combo > 1) {
    ctx.fillStyle = "#ff2bd6";
    ctx.font = "900 22px Impact, system-ui, sans-serif";
    ctx.fillText(S.combo + "x", W / 2, 70);
  }
  ctx.fillStyle = "#e8f6ff";
  ctx.font = "700 18px Impact, system-ui, sans-serif";
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
    ctx.font = "700 22px Impact, system-ui, sans-serif";
    ctx.fillStyle = "#00f0ff";
    ctx.letterSpacing = "0.2em";
    ctx.fillText("LIFT THE MOUSE", W / 2, H * 0.78);
    ctx.restore();
  }
}

function drawBayHUD() {
  ctx.save();
  const op = Locker.operator;
  ctx.font = "700 22px system-ui, sans-serif";
  ctx.fillStyle = Locker.colors.bone;
  ctx.textAlign = "left";
  ctx.fillText(`${op.displayName}  ${Bay.you}   —   ${Bay.them}   ·  ${Locker.equippedStyle.toUpperCase()}`, HUD_PAD, HUD_PAD + 20);

  const inWindow = Bay.pos.x < -4.8;
  const inAngle = Bay.pos.x > 4.6;
  const inOpen = !inWindow && !inAngle && Bay.pos.z < 8.0;
  let coverText = "PAD";
  let coverColor = Locker.colors.mint;
  if (inOpen && !Bay.frozen) {
    coverText = "DANGER: OPEN";
    coverColor = "#ff2bd6";
  } else if (inWindow) {
    coverText = "COVER: WINDOW";
    coverColor = Locker.colors.mint;
  } else if (inAngle) {
    coverText = "COVER: ANGLE";
    coverColor = Locker.colors.mint;
  } else if (S.lifted) {
    coverText = "LIFT";
    coverColor = Locker.colors.mint;
  }

  ctx.font = "700 13px system-ui, sans-serif";
  ctx.fillStyle = coverColor;
  ctx.fillText(coverText, HUD_PAD, HUD_PAD + 44);

  if (Bay.expose > 0 && !Bay.frozen) {
    ctx.fillStyle = "rgba(255, 43, 214, 0.2)";
    ctx.fillRect(HUD_PAD, HUD_PAD + 52, 120, 6);
    ctx.fillStyle = "#ff2bd6";
    ctx.fillRect(HUD_PAD, HUD_PAD + 52, 120 * clamp(Bay.expose / Bay.exposeMax, 0, 1), 6);
  }

  drawModeChip();

  if (Bay.voT > 0 && Bay.voText) {
    ctx.font = "italic 700 24px system-ui, sans-serif";
    ctx.fillStyle = Locker.colors.bone;
    ctx.textAlign = "center";
    ctx.fillText(`"${Bay.voText}"`, W * 0.5, H - 70);
  }

  ctx.font = "500 13px system-ui, sans-serif";
  ctx.fillStyle = "rgba(232, 246, 255, 0.55)";
  ctx.textAlign = "center";
  if (Bay.over) {
    ctx.fillText(`${Bay.you >= Bay.toWin ? "VICTORIA" : "DERROTA"} · ${op.vo.win} · Primer a 5`, W * 0.5, H - 32);
  } else if (Bay.frozen) {
    ctx.fillText("RONDA CONGELADA · BAJA EL RATÓN AL PAD PARA CONTINUAR", W * 0.5, H - 32);
  } else {
    ctx.fillText(`WASD en pad  ·  LEVANTA para bloquear paso y apuntar  ·  CLIC dispara  ·  L cambia estilo (${Locker.equippedStyle})`, W * 0.5, H - 32);
  }
  ctx.restore();
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
  }
}

// --- Main Render Loop ---
function draw2D(now) {
  ctx.clearRect(0, 0, W, H);
  if (phase === "lock") {
    drawModeChip();
  } else if (phase === "calibrate") {
    drawCalib(now);
    drawCrosshair(S.aim.x, S.aim.y);
    drawModeChip();
  } else if (phase === "range") {
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
  } else if (phase === "bay") {
    drawCrosshair(S.aim.x, S.aim.y);
    drawBayHUD();
  }
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
  if (phase === "range") updateRange(dt, t);
  if (phase === "bay") tickBay(dt);

  // Recoil decay & camera punch
  S.recoil += (0 - S.recoil) * Math.min(1, dt * 18);
  S.punch *= Math.max(0, 1 - dt * 14);

  // First-Person Gun 3D Pose: Lowered on pad, Raised in ADS when lifted
  if (gunGroup) {
    const targetY = S.lifted ? -0.16 : -0.24;
    const targetX = S.lifted ? 0.08 : 0.24;
    const targetZ = S.lifted ? -0.36 : -0.42;
    gunGroup.position.x += (targetX - gunGroup.position.x) * Math.min(1, dt * 14);
    gunGroup.position.y += (targetY - gunGroup.position.y) * Math.min(1, dt * 14);
    gunGroup.position.z += (targetZ - gunGroup.position.z) * Math.min(1, dt * 14);
    gunGroup.rotation.x += (0 - gunGroup.rotation.x) * Math.min(1, dt * 16);
  }
  if (gunMuzzleLight && gunMuzzleLight.intensity > 0) {
    gunMuzzleLight.intensity = Math.max(0, gunMuzzleLight.intensity - dt * 30);
  }

  // Decay 3D shards
  for (const s of S.parts) {
    s.age += dt;
    s.mesh.position.addScaledVector(s.vel, dt);
    s.vel.y -= 9.8 * dt;
    s.mesh.rotation.x += 4 * dt;
    s.mesh.rotation.y += 3 * dt;
  }
  for (let i = S.parts.length - 1; i >= 0; i--) {
    if (S.parts[i].age >= S.parts[i].life) {
      shardGroup.remove(S.parts[i].mesh);
      S.parts.splice(i, 1);
    }
  }

  // Decay bullet tracers
  for (let i = tracerLines.length - 1; i >= 0; i--) {
    tracerLines[i].age += dt;
    if (tracerLines[i].age >= tracerLines[i].life) {
      scene.remove(tracerLines[i].line);
      tracerLines.splice(i, 1);
    }
  }

  // 3D Scene Render
  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }

  // 2D Canvas HUD Overlay
  draw2D(t);
  syncCursor();
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

// --- Event Listeners & Input ---
canvasHUD.addEventListener("pointerdown", (e) => {
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
  if (phase === "range" || phase === "bay") {
    e.preventDefault();
    fire();
  }
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
  if (e.code === "KeyW") Bay.keys.w = true;
  if (e.code === "KeyA") Bay.keys.a = true;
  if (e.code === "KeyS") Bay.keys.s = true;
  if (e.code === "KeyD") Bay.keys.d = true;
  if (e.code === "KeyL") {
    const nextStyle = Locker.cycleStyle();
    Bay.vo("ESTILO: " + nextStyle.toUpperCase());
  }
});

window.addEventListener("keyup", (e) => {
  if (e.code === "Space") S.forceGun = false;
  if (e.code === "KeyW") Bay.keys.w = false;
  if (e.code === "KeyA") Bay.keys.a = false;
  if (e.code === "KeyS") Bay.keys.s = false;
  if (e.code === "KeyD") Bay.keys.d = false;
});

window.addEventListener("resize", fit);

$("btn-play").addEventListener("click", () => {
  S.online = false;
  S.playlist = "range";
  play("range");
});
const btnOnline = $("btn-online");
if (btnOnline) btnOnline.addEventListener("click", () => openLobby());
const btnLobbyRange = $("btn-lobby-range");
if (btnLobbyRange) btnLobbyRange.addEventListener("click", () => lobbyStartRange());
const btnLobbyJoin = $("btn-lobby-join");
if (btnLobbyJoin) {
  btnLobbyJoin.addEventListener("click", () => {
    const inp = $("lobby-join");
    const code = inp ? inp.value : "";
    lobbyJoin(code).catch((err) => {
      const tag = $("lobby-tag");
      if (tag) tag.textContent = String(err.message || err);
    });
  });
}
const btnLobbyBack = $("btn-lobby-back");
if (btnLobbyBack) btnLobbyBack.addEventListener("click", () => lobbyLeave());

const btnGemini = $("btn-gemini-lock");
if (btnGemini) btnGemini.addEventListener("click", () => { requestGeminiLock(); });

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
$("btn-again").addEventListener("click", () => enterGame());
$("btn-recal").addEventListener("click", () => {
  S.camPts = [null, null, null, null];
  S.H = null;
  S.desktop = false;
  S.lockAdvance = false;
  setPhase("calibrate");
});

function syncCursor() {
  const hide = phase === "range" || phase === "bay" || phase === "calibrate" || phase === "lock";
  canvas3D.classList.toggle("nocursor", hide);
  canvasHUD.classList.toggle("nocursor", hide);
  const v = hide ? "none" : "";
  document.body.style.cursor = v;
  document.documentElement.style.cursor = v;
}

// --- Initialize Engine ---
fit();
init3D();
S.aim.x = W / 2;
S.aim.y = H / 2;
fetch("/api/health").then((r) => r.json()).then((h) => {
  S.engine.mojo = h.mojo || null;
  S.engine.gemini = !!h.gemini;
}).catch(() => {});
requestAnimationFrame(frame);
