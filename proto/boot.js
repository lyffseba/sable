/* SABLE — boot.js
   Boot, lobby UI wiring, serve entry, phase machine glue.
   Trackpad / HID click fires from the AimBus mailbox — never waits on camera. */

import {
  S,
  W,
  H,
  dpr,
  phase,
  assignView,
  assignPhase,
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
  foeGroup,
  tracerLines,
  startRange,
  updateRange,
  tickBay,
  sharedMatch,
  applySharedSim,
  RANGE_MS,
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
  results: $("screen-results"),
};

const CORNER_NAMES = ["TOP LEFT", "TOP RIGHT", "BOTTOM RIGHT", "BOTTOM LEFT"];

export let stream = null, camReady = false, lastT = 0;
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
  if (kicker) kicker.textContent = data.phase === "wait" ? "5v5  ·  WAITING ARENA" : "5v5  ·  RANGE";
  const tag = $("lobby-tag");
  if (tag) {
    tag.textContent = S.host
      ? "WARM UP is practice now. ENTER RANGE shares one house — same plates."
      : "WARM UP anytime. Waiting on host for the shared house.";
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
  if (phase !== "lobby" && !S.warmup && !sharedMatch()) return;
  try {
    const res = await fetch("/api/lobby?code=" + encodeURIComponent(S.room));
    const data = await res.json();
    if (!data.ok) return;
    if (phase === "lobby" || S.warmup) paintLobby(data);
    if (data.phase === "range" && !lobbyStarting) {
      S.warmup = false;
      lobbyStarting = true;
      syncWarmupChrome();
      if (phase === "range") startRange();
      else if (phase === "results") setPhase("range");
      else if (phase === "lobby") play("range");
    }
    if (sharedMatch() && phase === "range" && data.phase === "range") {
      applySharedSim(data);
    }
  } catch (e) { /* keep polling */ }
}

async function lobbyStartRange() {
  S.warmup = false;
  syncWarmupChrome();
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
  ensureLobbyPoll();
  play("range");
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
  S.online = true;
  syncWarmupChrome();
  // Seat mark is best-effort. Do not wait on net to practice.
  lobbyPost("/api/lobby/warmup").then(function (data) {
    if (data && data.ok) paintLobby(data);
  });
  if (camReady && (S.smooth || S.tpl || S.desktop)) {
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

async function returnToLobby() {
  S.warmup = false;
  lobbyStarting = false;
  const playBtn = $("btn-play");
  if (playBtn) { playBtn.disabled = false; playBtn.textContent = "OFFLINE"; }
  const onBtn = $("btn-online");
  if (onBtn) onBtn.disabled = false;
  syncWarmupChrome();
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
  lobbyStarting = false;
  syncWarmupChrome();
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
    goDesktopRange();
    return;
  }
  await initHands();
  armVideoTrack();
  S.lockStart = performance.now();
}

function setPhase(next) {
  assignPhase(next);
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
  syncWarmupChrome();
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
  const sess = S.warmup
    ? "WARM UP  " + S.room
    : (sharedMatch()
      ? "SHARED  " + S.room
      : (!S.online ? "OFFLINE RANGE" : (S.playlist === "5v5" ? "5v5  " + S.room : "ONLINE RANGE")));
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
    ctx.fillText("RAISE YOUR HAND", W / 2, H * 0.78);
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
    ctx.fillText("RONDA CONGELADA · BAJA LA MANO PARA CONTINUAR", W * 0.5, H - 32);
  } else {
    ctx.fillText(`WASD en pad  ·  LEVANTA la mano para apuntar  ·  CLIC dispara  ·  L cambia estilo (${Locker.equippedStyle})`, W * 0.5, H - 32);
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
    maybePinchFire(S.handLm);
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
  S.warmup = false;
  S.playlist = "range";
  play("range");
});
const btnOnline = $("btn-online");
if (btnOnline) btnOnline.addEventListener("click", () => openLobby());
const btnLobbyRange = $("btn-lobby-range");
if (btnLobbyRange) btnLobbyRange.addEventListener("click", () => lobbyStartRange());
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
  requestGeminiLock,
};
