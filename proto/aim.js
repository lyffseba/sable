/* SABLE — aim.js
   AimSample / AimBus, fire peek, sticky lift, SablePerf, desktop fallback.
   SablePort verb seam: fire peeks AimBus. Later host adapters keep this peek.
   Trackpad / HID click fires from the AimBus mailbox — never waits on camera. */

import * as THREE from "./vendor/three.module.js";
import { detGood, PROC_W, PROC_H, COAST_MS } from "./hands.js";
import {
  bang,
  hitBlip,
  missTick,
  gunMuzzleLight,
  gunGroup,
  camera,
  rangeTargetGroup,
  fireBay3D,
  addBulletTracer,
  shatterTarget3D,
  worldToHud,
  popup,
  sharedMatch,
  sharedBay,
  reportSharedFire,
  reportSharedBayFire,
} from "./house.js";
import { enterGame } from "./boot.js";

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

// HID→hitscan probe. Off unless ?sableperf=1 or localStorage SablePerf=1.
// Not a HUD. window.SablePerf.stats() → { n, p50, p99, ok } vs 8 ms budget.
// Shared Bay report / pose / lobby poll stay after markHid — never inside this bar.
const SablePerf = {
  on: false,
  budgetMs: 8,
  cap: 128,
  hid: [],
  begin() {
    return this.on ? performance.now() : 0;
  },
  markHid(t0) {
    if (!this.on || !t0) return;
    this.hid.push(performance.now() - t0);
    if (this.hid.length > this.cap) this.hid.shift();
  },
  pct(sorted, p) {
    if (!sorted.length) return 0;
    const i = Math.min(sorted.length - 1, Math.ceil(p * sorted.length) - 1);
    return sorted[i];
  },
  stats() {
    const s = this.hid.slice().sort((a, b) => a - b);
    const p50 = this.pct(s, 0.5);
    const p99 = this.pct(s, 0.99);
    return { n: s.length, p50, p99, ok: !s.length || p99 < this.budgetMs };
  },
};
try {
  SablePerf.on = /(?:\?|&)sableperf=1(?:&|$)/.test(location.search)
    || (typeof localStorage !== "undefined" && localStorage.getItem("SablePerf") === "1");
} catch (e) { SablePerf.on = false; }
if (typeof globalThis !== "undefined") globalThis.SablePerf = SablePerf;

const HID_IDLE_MS = 40;
const LIFT_ON_MS = 50;
// Recent landmark / good AimSample owns GUN through a MacBook pad reach.
// Coast UV stays 100 ms (do not invent pose). Lift sticks longer.
const LIFT_STICKY_MS = 550;
const LIFT_HID_HOLD_MS = 180;

export let W = 1280, H = 720, dpr = 1, phase = "boot";

// Durable hangar session — not the screen/sim phase.
// hangar: boot / Offline gallery. wait_practice: HUD-on-Yard + WARM UP.
// match_live: shared ENTER RANGE. Server room.phase stays wait|range|bay.
export const HANGAR_PHASES = ["hangar", "wait_practice", "match_live"];

export function assignView(w, h, ratio) {
  W = w; H = h; dpr = ratio;
}

export function assignPhase(next) {
  phase = next;
}

export function assignHangar(next) {
  if (next !== "hangar" && next !== "wait_practice" && next !== "match_live") {
    throw new Error("SABLE HANGAR: unknown hangar phase " + next);
  }
  S.hangar = next;
}

const S = {
  det: null, smooth: null, vel: { x: 0, y: 0 }, lastDetAt: 0, trackT: 0,
  camStamp: -1, quality: 0, euroX: null, euroY: null, lastRaw: null, seeking: false,
  H: null, useBilinear: false, camPts: [null, null, null, null], calibIndex: 0,
  calibFlash: 0, forceGun: false, desktop: false, hidLast: 0, hidMoving: false,
  mode: "PAD", lifted: false, liftMs: 0, liftTick: 0, aim: { x: 0.5, y: 0.5 },
  recoil: 0, punch: 0, flash: 0, hitstop: 0,
  orbs: [], parts: [], pops: [], score: 0, hits: 0, shots: 0, combo: 0, comboMax: 0,
  rangeStart: 0, simTick: 0, simHz: 128,
  lockSince: 0, locked: false, lockStart: 0, lockAdvance: false,
  noLockFlash: 0, liftPulse: 0, enteringRange: false,
  tpl: null, ncc: 0, gray: null, skin: null, frame: null, lockHand: null,
  lockAcc: null, lockAccCols: 0, lockAccRows: 0,
  lockBestScore: 0, lockBestPatch: null, lockBestTL: null, lockTplAt: 0,
  engine: { mojo: null, gemini: false, hands: false, handsWorker: false },
  handsOn: false, hands: null, mpTs: 0, pinchHeld: false, handLm: null, rvfc: false,
  mpBusy: false, mpDelegate: "",
  online: false,
  playlist: "gallery",
  room: "",
  player: "",
  slot: -1,
  host: false,
  warmup: false,
  waitingYard: false,
  hangar: "hangar",
  seed: 0,
  sharedDead: null,
  sharedPending: null,
  bayMatch: false,
  baySeat: "A",
  bayFoe: "",
};

function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
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
// --- Mode & Aim Mailbox Wiring ---
function updateMode(now) {
  S.hidMoving = now - S.hidLast < HID_IDLE_MS;
  const since = S.lastDetAt ? now - S.lastDetAt : 1e9;
  const coasting = !!S.smooth && since <= COAST_MS;
  const recent = !!S.smooth && since <= LIFT_STICKY_MS;
  const locked = detGood() || coasting;
  const handOwns = detGood() || recent;
  const dtm = S.liftTick ? Math.min(40, now - S.liftTick) : 16;
  S.liftTick = now;
  if (S.desktop) {
    S.mode = "DESKTOP"; S.seeking = false; S.lifted = true; S.liftMs = LIFT_ON_MS; return;
  }
  // Hand-visible / recent sample owns lift. HID click must not demote GUN.
  const want = S.forceGun || handOwns;
  const holdClick = S.liftMs >= LIFT_ON_MS && S.hidMoving && since <= LIFT_STICKY_MS + LIFT_HID_HOLD_MS;
  if (want) S.liftMs = Math.min(160, S.liftMs + dtm);
  else if (!holdClick) S.liftMs = Math.max(0, S.liftMs - dtm);
  S.lifted = S.forceGun || S.liftMs >= LIFT_ON_MS;
  if (aimBus.peek()) {
    aimBus.peek().lifted = S.lifted;
  }
  if (S.forceGun) {
    S.mode = "GUN"; S.seeking = !locked; return;
  }
  if (S.lifted || handOwns) {
    S.mode = "GUN"; S.seeking = !locked && !S.lifted; return;
  }
  if (S.hidMoving) {
    S.mode = "PAD"; S.seeking = true; return;
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
  if (phase !== "range" && phase !== "calibrate" && phase !== "bay" && phase !== "lock" && phase !== "lobby") return;
  if (S.H || S.camPts.every(Boolean)) {
    const p = camToScreen(S.smooth.x, S.smooth.y);
    if (!p.lost) publishAim(p.x, p.y);
    else S.seeking = true;
  } else {
    publishAim((S.smooth.x / PROC_W) * W, (S.smooth.y / PROC_H) * H);
  }
}
// --- HID Fire Contract & Hitscan ---
function fire() {
  if (phase !== "range" && phase !== "bay" && phase !== "lobby" && !(phase === "calibrate" && S.calibIndex >= 4)) return;
  // Peek first. Never wait on a camera frame. Never recompute aim on click.
  const shot = aimBus.fire();
  const now = performance.now();
  const since = S.lastDetAt ? now - S.lastDetAt : 1e9;
  const recent = !!S.smooth && since <= LIFT_STICKY_MS;
  const busLift = !!(shot && shot.lifted);
  if (!S.desktop && !S.lifted && !busLift && !recent && !S.forceGun) return;

  // Probe HID→hitscan from post-gate, including bang path + gun FX, to first intersect.
  const t0 = SablePerf.begin();
  bang();
  S.recoil = 2.4; S.flash = 0.06; S.punch = 1.8;

  // Gun recoil animation & muzzle flash in 3D
  if (gunMuzzleLight) gunMuzzleLight.intensity = 3.5;
  if (gunGroup) {
    gunGroup.position.z += 0.07;
    gunGroup.rotation.x += 0.15;
  }

  // Hitscan uses last committed S.aim / AimBus sample. Track loop already published.
  const mouseNorm = new THREE.Vector2((S.aim.x / W) * 2 - 1, -(S.aim.y / H) * 2 + 1);
  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera(mouseNorm, camera);

  const muzzleWorld = new THREE.Vector3();
  gunMuzzleLight.getWorldPosition(muzzleWorld);

  if (phase === "bay") {
    fireBay3D(raycaster, muzzleWorld);
    SablePerf.markHid(t0);
    // Shared Bay POST is after the 8 ms HID→hitscan mark — fire-and-forget.
    if (sharedBay()) {
      try { reportSharedBayFire(shot); } catch (e) { /* local already resolved */ }
    }
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
    SablePerf.markHid(t0);
    return;
  }

  S.shots++;
  let hit = null;
  const hits = raycaster.intersectObjects(rangeTargetGroup.children, true);
  SablePerf.markHid(t0);
  if (hits.length) {
    let obj = hits[0].object;
    while (obj && !obj.userData.orb) obj = obj.parent;
    hit = obj && obj.userData.orb;
  }

  if (hit && hit.mesh) {
    S.combo++;
    if (S.combo > S.comboMax) S.comboMax = S.combo;
    const pts = hit.worth * S.combo;
    S.score += pts; S.hits++;
    const hitPos = hit.mesh.position.clone();
    hitBlip(S.combo, hitPos.x); S.hitstop = 1;
    addBulletTracer(muzzleWorld, hitPos);
    shatterTarget3D(hitPos, hit.hue);
    const hud = worldToHud(hitPos);
    popup(hud.x, hud.y - 18, (S.combo > 1 ? S.combo + "x " : "") + pts, hit.hue);

    rangeTargetGroup.remove(hit.mesh);
    S.orbs = S.orbs.filter((o) => o !== hit);
  } else {
    S.combo = 0;
    const farPoint = raycaster.ray.origin.clone().add(raycaster.ray.direction.clone().multiplyScalar(20));
    missTick(farPoint.x);
    addBulletTracer(muzzleWorld, farPoint);
  }
  // Shared report never gates the shot. Net down → local shatter still happened.
  if (sharedMatch()) {
    try { reportSharedFire(shot, hit && hit.id); } catch (e) { /* local already resolved */ }
  }
}
function goDesktopRange() {
  if (S.lockAdvance) return;
  S.lockAdvance = true;
  S.desktop = true;
  S.mode = "DESKTOP";
  enterGame();
}

export {
  AimSample,
  AimBus,
  aimBus,
  SablePerf,
  HID_IDLE_MS,
  LIFT_ON_MS,
  LIFT_STICKY_MS,
  LIFT_HID_HOLD_MS,
  S,
  clamp,
  solveLinear,
  dltHomography,
  screenCorners,
  computeH,
  camToScreen,
  updateMode,
  publishAim,
  updateAim,
  fire,
  goDesktopRange,
};
