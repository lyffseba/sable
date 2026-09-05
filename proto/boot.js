/* SABLE — boot.js
   Boot, lobby UI wiring, serve entry, phase machine glue.
   Durable hangar session: S.hangar hangar | wait_practice | match_live.
   SablePort tick/playlist seam: 128 Hz stepSim; HID fire outside. Playlist:
   docs/modes.md. Port path: docs/port.md.
   Trackpad / HID click fires from the AimBus mailbox — never waits on camera. */

import {
  S,
  W,
  H,
  dpr,
  phase,
  assignView,
  assignPhase,
  assignHangar,
  publishAim,
  updateMode,
  updateAim,
  fire,
  goDesktopRange,
  clamp,
  screenCorners,
  computeH,
} from "./aim.js";
import {
  grabFrame,
  runTrack,
  coastTrack,
  maybePinchFire,
  initHands,
  armVideoTrack,
  resetTrackFilters,
  detGood,
  sizeProc,
  commitTpl,
  PROC_W,
  PROC_H,
  TPL,
  COAST_MS,
  LOCK_SAMPLE_MS,
  LOCK_CONFIRM_MS,
  LOCK_GIVE_MS,
  TPL_FAIL_MS,
} from "./hands.js";
import {
  Locker,
  Bay,
  speak,
  unlockAudio,
  afterLiftState,
  hitBlip,
  init3D,
  renderer,
  scene,
  camera,
  gunGroup,
  gunMuzzleLight,
  rangeTargetGroup,
  rangeHallGroup,
  shardGroup,
  bayGroup,
  tracerLines,
  startRange,
  startWaitingYard,
  startBay,
  restoreYardLook,
  applyLockerLook,
  updateRange,
  tickBay,
  sharedMatch,
  sharedBay,
  applySharedSim,
  applySharedBay,
  reportSharedBayPose,
  bayCoverChip,
  galleryLeftMs,
  gallerySessionLabel,
  bayOver,
  baySessionLabel,
  HUD_PAD,
} from "./house.js";

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
  bay: $("screen-bay"),
  results: $("screen-results"),
};

const CORNER_NAMES = ["TOP LEFT", "TOP RIGHT", "BOTTOM RIGHT", "BOTTOM LEFT"];

export let stream = null, camReady = false, lastT = 0;
const SIM_HZ = 128;
const SIM_DT = 1 / SIM_HZ;
let simAcc = 0;
let targetGameMode = "range";
let geminiLockPending = false;
let geminiAutoTried = false;

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
    const tip = data.fingertip || data.muzzle_point;
    if (data.detected && tip && phase === "lock") {
      const mx = clamp((tip[1] / 1000) * PROC_W, 0, PROC_W - 1);
      const my = clamp((tip[0] / 1000) * PROC_H, 0, PROC_H - 1);
      const now = performance.now();
      commitTpl(S.gray, PROC_W, PROC_H, Math.round(mx - TPL * 0.5), Math.round(my - TPL * 0.5), now);
      S.quality = clamp((data.confidence || 0.95) * 100, 0, 100);
      S.locked = true;
      if (st) st.textContent = "HAND LOCKED";
      hitBlip(2);
      speak(data.gesture ? "Mano: " + data.gesture : "Mano fijada.");
      setTimeout(() => { if (phase === "lock") goCalib(); }, 500);
      geminiLockPending = false;
      return true;
    }
  } catch (err) {
    console.warn("Gemini hand lock fallback:", err);
  }
  geminiLockPending = false;
  if (st && phase === "lock" && !S.locked) st.textContent = "SEEKING";
  return false;
}
function enterGame() {
  setPhase(targetGameMode === "bay" ? "bay" : "range");
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
  S.tpl = null; S.ncc = 0; S.det = null; S.lockHand = null;
  S.lockAcc = null; S.lockBestScore = 0; S.lockBestPatch = null; S.lockBestTL = null;
  S.lockTplAt = 0; S.lockSince = 0; S.locked = false; S.lockAdvance = false;
  S.desktop = false; S.mode = "SEEKING"; S.smooth = null;
  S.lifted = false; S.liftMs = 0; S.liftTick = 0; S.pinchHeld = false;
  resetTrackFilters();
}
let lobbyTimer = 0;
let lobbyStarting = false;

function stopLobbyPoll() {
  if (lobbyTimer) { clearInterval(lobbyTimer); lobbyTimer = 0; }
}

function ensureLobbyPoll() {
  if (!S.room || !S.online) return;
  if (!lobbyTimer) lobbyTimer = setInterval(lobbyPoll, 200);
}
function slotLabel(slot) {
  if (!slot) return "—";
  const you = slot.id === S.player ? "YOU  " : "";
  const warm = slot.warmup ? "  ·  WARM" : "";
  return you + slot.name + warm;
}

function paintLobby(data) {
  if (!data || !data.ok) return;
  S.room = data.code;
  S.host = data.host === S.player;
  S.playlist = "5v5";
  const room = $("lobby-room");
  if (room) room.textContent = "ROOM  " + data.code;
  const kicker = $("lobby-kicker");
  if (kicker) kicker.textContent = data.phase === "wait" ? "5v5  ·  YARD" : "5v5  ·  GALLERY";
  const tag = $("lobby-tag");
  if (tag) {
    tag.textContent = S.host
      ? "Yard is live. WARM UP is practice. ENTER RANGE shares the gallery."
      : "Yard is live. WARM UP anytime. Host ENTER RANGE shares the gallery.";
  }
  const el = $("lobby-slots");
  if (el && data.slots) {
    const rows = ["<b>ALPHA</b><b>BRAVO</b>"];
    for (let i = 0; i < 5; i++) {
      const A = data.slots[i];
      const B = data.slots[i + 5];
      rows.push(
        "<span class=\"" + (A && A.id === S.player ? "you" : "") + "\">" + (i + 1) + "  " + slotLabel(A) + "</span>" +
        "<span class=\"" + (B && B.id === S.player ? "you" : "") + "\">" + (i + 6) + "  " + slotLabel(B) + "</span>"
      );
    }
    el.innerHTML = rows.join("");
  }
  const enter = $("btn-lobby-range");
  if (enter) enter.hidden = !S.host && data.phase === "wait";
  const warm = $("btn-lobby-warmup");
  if (warm) warm.hidden = data.phase !== "wait";
  const lobbyBay = $("btn-lobby-bay");
  if (lobbyBay) lobbyBay.hidden = true;
  syncWarmupChrome();
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
  ensureLobbyPoll();
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
  ensureLobbyPoll();
}

async function lobbyPoll() {
  if (!S.room || !S.online) return;
  if (phase === "bay") {
    if (!sharedBay()) return;
    try {
      const res = await fetch("/api/lobby?code=" + encodeURIComponent(S.room));
      const data = await res.json();
      if (!data.ok) return;
      if (data.phase === "bay") {
        reportSharedBayPose();
        applySharedBay(data);
      }
    } catch (e) { /* keep polling */ }
    return;
  }
  if (phase !== "lobby" && !S.warmup && !sharedMatch() && !sharedBay()) return;
  try {
    const res = await fetch("/api/lobby?code=" + encodeURIComponent(S.room));
    const data = await res.json();
    if (!data.ok) return;
    if (phase === "lobby" || S.warmup) paintLobby(data);
    if (data.phase === "bay" && !lobbyStarting) {
      S.warmup = false;
      S.bayMatch = true;
      S.playlist = "bay";
      if (data.seats && S.player && data.seats[S.player]) S.baySeat = data.seats[S.player];
      lobbyStarting = true;
      syncWarmupChrome();
      applySharedBay(data);
      if (phase === "lobby") play("bay");
      else if (phase === "results") setPhase("bay");
    }
    if (data.phase === "range" && !lobbyStarting) {
      S.warmup = false;
      lobbyStarting = true;
      syncWarmupChrome();
      assignHangar("match_live");
      if (phase === "range") startRange();
      else if (phase === "results") setPhase("range");
      else if (phase === "lobby") enterRangePreserve();
    }
    if (sharedMatch() && phase === "range" && data.phase === "range") {
      applySharedSim(data);
    }
    if (sharedBay() && data.phase === "bay") {
      applySharedBay(data);
    }
  } catch (e) { /* keep polling */ }
}

function alreadyLifted() {
  return !!(camReady && (S.smooth || S.tpl || S.desktop));
}

function enterRangePreserve() {
  // SableNet phase-preserve: live Yard skips calib/lock so HID stays warm.
  assignHangar("match_live");
  if (alreadyLifted() || phase === "lobby" || phase === "range") {
    setPhase("range");
    return;
  }
  play("range");
}

function lobbyStartRange() {
  S.warmup = false;
  S.waitingYard = false;
  syncWarmupChrome();
  if (S.room && S.player) {
    if (S.host) lobbyPost("/api/lobby/start");
    lobbyStarting = true;
    ensureLobbyPoll();
  }
  enterRangePreserve();
}

async function lobbyPost(path) {
  if (!S.room || !S.player) return null;
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: S.room, player: S.player }),
    });
    return await res.json();
  } catch (e) {
    return null;
  }
}

async function lobbyWarmup() {
  if (!S.room || !S.player) {
    play("range");
    return;
  }
  S.warmup = true;
  S.waitingYard = false;
  S.online = true;
  assignHangar("wait_practice");
  syncWarmupChrome();
  // Seat mark is best-effort. Do not wait on net to practice.
  lobbyPost("/api/lobby/warmup").then(function (data) {
    if (data && data.ok) paintLobby(data);
  });
  if (alreadyLifted()) {
    setPhase("range");
    return;
  }
  play("range");
}

function syncWarmupChrome() {
  const bar = $("range-warmup-bar");
  if (bar) bar.hidden = !S.warmup;
  const res = $("btn-results-lobby");
  if (res) res.hidden = !S.warmup;
}

function syncBayChrome() {
  const bar = $("bay-bar");
  if (bar) bar.hidden = phase !== "bay";
  const boot = $("btn-bay-boot");
  if (boot) boot.textContent = S.online ? "RETURN TO LOBBY" : "BOOT";
}

function lobbyStartBay() {
  S.playlist = "bay";
  S.warmup = false;
  S.waitingYard = false;
  syncWarmupChrome();
  if (S.room && S.player) {
    S.bayMatch = true;
    if (S.host) lobbyPost("/api/lobby/bay");
    ensureLobbyPoll();
  }
  if (alreadyLifted()) {
    setPhase("bay");
    return;
  }
  play("bay");
}

function leaveBay() {
  Bay.active = false;
  syncBootButtons(false);
  if (S.online) {
    returnToLobby();
    return;
  }
  setPhase("boot");
}

async function returnToLobby() {
  S.warmup = false;
  S.waitingYard = false;
  S.bayMatch = false;
  S.bayFoe = "";
  S.baySeat = "A";
  lobbyStarting = false;
  const playBtn = $("btn-play");
  if (playBtn) { playBtn.disabled = false; playBtn.textContent = "OFFLINE"; }
  const onBtn = $("btn-online");
  if (onBtn) onBtn.disabled = false;
  syncWarmupChrome();
  syncBootButtons(false);
  setPhase("lobby");
  stopLobbyPoll();
  ensureLobbyPoll();
  lobbyPost("/api/lobby/resume").then(function (data) {
    if (data && data.ok) paintLobby(data);
  });
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
  S.warmup = false;
  S.waitingYard = false;
  S.bayMatch = false;
  S.bayFoe = "";
  S.baySeat = "A";
  lobbyStarting = false;
  syncWarmupChrome();
  syncBootButtons(false);
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

function syncBootButtons(busy) {
  const playBtn = $("btn-play");
  if (playBtn) {
    playBtn.disabled = !!busy;
    if (!busy) playBtn.textContent = "OFFLINE";
  }
  const onBtn = $("btn-online");
  if (onBtn) onBtn.disabled = !!busy;
  const bayBtn = $("btn-bay");
  if (bayBtn) {
    bayBtn.hidden = true;
    bayBtn.disabled = true;
  }
}

async function play(target = "range") {
  targetGameMode = target === "bay" ? "bay" : "range";
  S.playlist = targetGameMode === "bay" ? "bay" : "gallery";
  unlockAudio();
  const playBtn = $("btn-play");
  if (playBtn) {
    playBtn.disabled = true;
    playBtn.textContent = "...";
  }
  syncBootButtons(true);
  resetLockState();
  setPhase("lock");
  S.lockStart = performance.now();
  const ok = await enableCamera();
  if (!ok) {
    goDesktopRange();
    return;
  }
  await initHands();
  armVideoTrack();
  S.lockStart = performance.now();
}

function syncHangar(screen) {
  // Screen/sim phase stays boot|lobby|range|… Hangar is the session class.
  // Sync only — never await, never touch AimBus / HID.
  if (screen === "boot") {
    assignHangar("hangar");
    return;
  }
  if (screen === "lobby") {
    assignHangar("wait_practice");
    return;
  }
  if (screen === "range") {
    if (S.warmup || S.waitingYard) assignHangar("wait_practice");
    else if (S.online && S.room && S.player && !S.bayMatch) assignHangar("match_live");
    else assignHangar("hangar");
  }
}

function setPhase(next) {
  assignPhase(next);
  syncHangar(next);
  for (const k of Object.keys(screens)) {
    if (screens[k]) screens[k].hidden = k !== next;
  }
  if (rangeTargetGroup) rangeTargetGroup.visible = (next === "range" || next === "lobby");
  if (rangeHallGroup) rangeHallGroup.visible = (next !== "bay");
  if (bayGroup) bayGroup.visible = (next === "bay");

  if (next === "calibrate") {
    S.calibIndex = S.camPts.every(Boolean) ? 4 : firstMissingCorner();
    updateCalibMsg();
    $("btn-redo").hidden = !S.camPts.some(Boolean) || S.calibIndex >= 4;
  }
  if (next === "range") startRange();
  else if (next === "bay") startBay();
  else if (next === "lobby") startWaitingYard();
  else if (next !== "lock" && next !== "calibrate") restoreYardLook();
  syncWarmupChrome();
  syncBayChrome();
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
function showResults() {
  const acc = S.shots ? Math.round((S.hits / S.shots) * 100) : 0;
  $("stats").innerHTML = [
    ["SCORE", S.score], ["HITS", S.hits], ["ACCURACY", acc + "%"],
    ["COMBO", S.comboMax], ["ROUND", "60s"],
  ].map(([k, v]) => "<div class=\"stat\"><b>" + v + "</b><span>" + k + "</span></div>").join("");
}

function tickLock(t) {
  const st = $("lock-status");
  if (!camReady) {
    if (st) st.textContent = "SEEKING";
    if (t - (S.lockStart || t) > LOCK_GIVE_MS) goDesktopRange();
    return;
  }
  if (t - (S.lockStart || t) > LOCK_GIVE_MS && !S.lockAdvance) {
    if (S.smooth || S.tpl) goCalib();
    else goDesktopRange();
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
    if (st) st.textContent = "HAND LOCKED";
    if (!S.lockSince) S.lockSince = t;
    S.locked = t - S.lockSince >= LOCK_CONFIRM_MS;
    if (S.locked) goCalib();
  } else {
    S.lockSince = 0;
    S.locked = false;
    if (st) st.textContent = "SEEKING";
  }
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
  assignView(window.innerWidth, window.innerHeight, Math.min(2, window.devicePixelRatio || 1));

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
  const qCol = q >= 70 ? Locker.colors.mint : q >= 40 ? "#ffd56a" : Locker.colors.rust;
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
  const handOn = !!S.engine.hands;
  const mLabel = mojoOn ? "MOJO 1.0" : "MOJO OFF";
  const gLabel = gemOn ? "GEMINI" : "GEMINI OFF";
  const hLabel = handOn ? "HANDS" : "HANDS OFF";
  ex -= ctx.measureText(hLabel).width + 18;
  chip(hLabel, handOn, ex);
  ex -= 8 + ctx.measureText(gLabel).width + 18;
  chip(gLabel, gemOn, ex);
  ex -= 8 + ctx.measureText(mLabel).width + 18;
  chip(mLabel, mojoOn, ex);
  ctx.restore();
}

// SableHUD bar — thin arcade chips. Charcoal plate, bone/mint/rust ink. No bloom.
const SABLE_HUD_H = 22;

function sableChipWidth(text) {
  ctx.font = "700 11px system-ui, sans-serif";
  ctx.letterSpacing = "0.12em";
  return Math.ceil(ctx.measureText(text).width) + 18;
}

function drawSableChip(text, col, x, y) {
  const w = sableChipWidth(text);
  ctx.fillStyle = "rgba(10,12,16,0.82)";
  ctx.strokeStyle = col;
  ctx.lineWidth = 1;
  ctx.fillRect(x, y, w, SABLE_HUD_H);
  ctx.strokeRect(x, y, w, SABLE_HUD_H);
  ctx.fillStyle = col;
  ctx.font = "700 11px system-ui, sans-serif";
  ctx.letterSpacing = "0.12em";
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(text, x + 9, y + SABLE_HUD_H * 0.5);
  ctx.letterSpacing = "0";
  return w;
}

// Readable hangar chips from S.hangar only — do not rename screen phases.
function hangarHudChip() {
  const h = S.hangar;
  if (h === "wait_practice") return ["WAIT", Locker.colors.bone];
  if (h === "match_live") return ["LIVE", Locker.colors.rust];
  if (h === "hangar") return ["READY", Locker.colors.mint];
  throw new Error("SABLE HUD: unknown hangar " + h);
}

function drawHUD(now) {
  drawModeChip();
  if (phase !== "range" && phase !== "lobby") return;
  const hangarChip = hangarHudChip();
  const left = galleryLeftMs(simMs());
  const sec = (left / 1000).toFixed(1);
  const sess = gallerySessionLabel();
  const bone = Locker.colors.bone;
  const mint = Locker.colors.mint;
  const rust = Locker.colors.rust;
  const timeCol = left <= 10000 ? rust : mint;
  let stateChip = "60s GALLERY";
  if (left <= 0) stateChip = "GALLERY CLEAR";
  else if (sess !== "GALLERY") stateChip = sess;
  const chips = [hangarChip];
  if (phase === "range") chips.push(["SCORE " + S.score, bone]);
  if (phase === "range" && S.combo > 1) chips.push([S.combo + "x", rust]);
  if (phase === "range") chips.push(["ROUND " + sec, timeCol]);
  if (phase === "range") chips.push([stateChip, left <= 10000 ? rust : mint]);
  ctx.save();
  const gap = 8;
  let total = 0;
  for (let i = 0; i < chips.length; i++) total += sableChipWidth(chips[i][0]) + gap;
  total -= gap;
  let x = Math.round((W - total) * 0.5);
  const y = HUD_PAD;
  for (let i = 0; i < chips.length; i++) {
    x += drawSableChip(chips[i][0], chips[i][1], x, y) + gap;
  }
  ctx.restore();
}

function drawBayHUD() {
  // Same thin SableHUD bar as gallery. Score / round / first-to-5. No tutorial wall.
  const bone = Locker.colors.bone;
  const mint = Locker.colors.mint;
  const rust = Locker.colors.rust;
  const cover = bayCoverChip(Bay.pos.x, Bay.pos.z, S.lifted, Bay.frozen, Bay.over);
  const coverCol = cover === "OPEN" ? rust : cover === "DROP" ? bone : mint;
  const state = baySessionLabel();
  const chips = [
    ["YOU " + Bay.you, bone],
    ["THEM " + Bay.them, rust],
    ["ROUND " + Bay.round, mint],
    [cover, coverCol],
    [state, bayOver() ? rust : mint],
  ];
  if (Bay.voT > 0 && Bay.voText) chips.push([Bay.voText, bone]);
  ctx.save();
  const gap = 8;
  let total = 0;
  for (let i = 0; i < chips.length; i++) total += sableChipWidth(chips[i][0]) + gap;
  total -= gap;
  let x = Math.round((W - total) * 0.5);
  const y = HUD_PAD;
  for (let i = 0; i < chips.length; i++) {
    x += drawSableChip(chips[i][0], chips[i][1], x, y) + gap;
  }
  ctx.restore();
  drawModeChip();
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
    if (S.aim) drawCrosshair(S.aim.x, S.aim.y);
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
  } else if (phase === "lobby") {
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

function simMs() {
  return S.simTick * (1000 / SIM_HZ);
}

function stepSim() {
  // Plates / Bay pose only. HID fire is not here. No rAF present.
  S.simTick += 1;
  if (phase === "range" || phase === "lobby") updateRange(SIM_DT, simMs());
  if (phase === "bay") tickBay(SIM_DT);
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
    maybePinchFire(S.handLm);
  }
  afterLiftState();

  if (phase === "lock") tickLock(t);
  if (phase === "range" || phase === "bay" || phase === "lobby") {
    simAcc += dt;
    if (simAcc > 0.25) simAcc = 0.25;
    while (simAcc >= SIM_DT) {
      stepSim();
      simAcc -= SIM_DT;
    }
  } else {
    simAcc = 0;
  }

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
  if (phase === "range" || phase === "bay" || phase === "lobby") {
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
  if (e.code === "Space") { e.preventDefault(); S.forceGun = true; afterLiftState(); }
  if (e.code === "KeyT") {
    if (phase === "lock") { goDesktopRange(); afterLiftState(); return; }
    S.desktop = !S.desktop;
    if (S.desktop) S.mode = "DESKTOP";
    afterLiftState();
  }
  if (e.code === "KeyW") Bay.keys.w = true;
  if (e.code === "KeyA") Bay.keys.a = true;
  if (e.code === "KeyS") Bay.keys.s = true;
  if (e.code === "KeyD") Bay.keys.d = true;
  if (e.code === "KeyL" && phase === "bay") {
    Locker.cycleStyle();
    applyLockerLook();
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
  S.warmup = false;
  S.waitingYard = false;
  S.playlist = "gallery";
  assignHangar("hangar");
  play("range");
});
const btnOnline = $("btn-online");
if (btnOnline) btnOnline.addEventListener("click", () => openLobby());
const btnLobbyRange = $("btn-lobby-range");
if (btnLobbyRange) btnLobbyRange.addEventListener("click", () => lobbyStartRange());
const btnBayBoot = $("btn-bay-boot");
if (btnBayBoot) btnBayBoot.addEventListener("click", () => leaveBay());
const btnLobbyWarmup = $("btn-lobby-warmup");
if (btnLobbyWarmup) btnLobbyWarmup.addEventListener("click", () => lobbyWarmup());
const btnReturnLobby = $("btn-return-lobby");
if (btnReturnLobby) btnReturnLobby.addEventListener("click", () => returnToLobby());
const btnResultsLobby = $("btn-results-lobby");
if (btnResultsLobby) btnResultsLobby.addEventListener("click", () => returnToLobby());
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
const btnSkipLock = $("btn-skip-lock");
if (btnSkipLock) btnSkipLock.addEventListener("click", () => {
  if (S.smooth || S.tpl) goCalib();
  else goDesktopRange();
});

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
  const hide = phase === "range" || phase === "bay" || phase === "lobby" || phase === "calibrate" || phase === "lock";
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
initHands();
requestAnimationFrame(frame);

export {
  $,
  cam,
  proc,
  canvas3D,
  canvasHUD,
  ctx,
  pctx,
  screens,
  CORNER_NAMES,
  enterGame,
  goCalib,
  resetLockState,
  stopLobbyPoll,
  ensureLobbyPoll,
  setPhase,
  play,
  lobbyStartBay,
  leaveBay,
  requestGeminiLock,
  SIM_HZ,
  SIM_DT,
  simMs,
  stepSim,
};
