/* SABLE — house.js
   Salt House / Yard Range, plates, shared match client hooks, Bay.
   Trackpad / HID click fires from the AimBus mailbox — never waits on camera. */

import * as THREE from "./vendor/three.module.js";
import { S, W, H, dpr, phase, aimBus, clamp } from "./aim.js";
import { $, canvas3D, setPhase, ensureLobbyPoll } from "./boot.js";

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

const RANGE_MS = 60000;
const SIT_DWELL_S = 4.2;
const SIT_DROP_VY = -3.2;
const PLATE_MAX_LIFE_S = 7.5;
const HUD_PAD = 16;

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

function pullWhistle() {
  if (!actx) return;
  const t = actx.currentTime;
  const osc = actx.createOscillator();
  const gain = actx.createGain();
  osc.type = "sine";
  osc.frequency.setValueAtTime(740, t);
  osc.frequency.exponentialRampToValueAtTime(1480, t + 0.11);
  gain.gain.setValueAtTime(0.12, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + 0.14);
  osc.connect(gain);
  gain.connect(actx.destination);
  osc.start(t);
  osc.stop(t + 0.15);
}

// ==========================================
// --- Three.js 3D Engine Architecture ---
// ==========================================
export let renderer, scene, camera;
export let gunGroup, gunBody, gunStripe, gunMuzzleLight;
export let rangeTargetGroup, rangeHallGroup, shardGroup;
export let bayGroup, foeGroup, foeMesh, foeVisor;
export let tracerLines = [];

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
  scene.background = new THREE.Color(0x151c22);
  scene.fog = new THREE.FogExp2(0x151c22, 0.022);

  camera = new THREE.PerspectiveCamera(62, W / H, 0.08, 160);
  camera.position.set(0, 1.64, 2.05);
  camera.lookAt(0, 0.55, -12);

  scene.add(new THREE.HemisphereLight(0x8aa8b8, 0x1a1810, 0.7));
  const dir = new THREE.DirectionalLight(0xe8dcc8, 1.15);
  dir.position.set(-6, 16, 4);
  scene.add(dir);
  const rim = new THREE.DirectionalLight(Locker.colors.mintHex, 0.22);
  rim.position.set(8, 5, -6);
  scene.add(rim);

  buildFirstPersonGun();
  buildRange3D();
  buildBay3D();
}

function sableStd(hex, extra) {
  return new THREE.MeshStandardMaterial(Object.assign({
    color: hex, roughness: 0.64, metalness: 0.14, flatShading: true,
  }, extra || {}));
}

function hexPlateGeo(r, thick) {
  const sh = new THREE.Shape();
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 - Math.PI / 6;
    const x = Math.cos(a) * r, y = Math.sin(a) * r;
    if (i === 0) sh.moveTo(x, y); else sh.lineTo(x, y);
  }
  sh.closePath();
  const g = new THREE.ExtrudeGeometry(sh, { depth: thick, bevelEnabled: false });
  g.rotateX(-Math.PI / 2);
  g.center();
  return g;
}

function buildFirstPersonGun() {
  gunGroup = new THREE.Group();
  const bone = sableStd(Locker.colors.boneHex, { roughness: 0.5 });
  const rust = sableStd(Locker.colors.rustHex, { roughness: 0.72 });
  const char = sableStd(0x141a22, { metalness: 0.35, roughness: 0.4 });
  const mint = new THREE.MeshBasicMaterial({ color: Locker.colors.mintHex });

  const cuff = new THREE.Mesh(new THREE.CylinderGeometry(0.046, 0.05, 0.07, 8), rust);
  cuff.rotation.x = Math.PI / 2;
  cuff.position.set(0, -0.01, 0.1);
  gunGroup.add(cuff);

  gunBody = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.045, 0.12), bone);
  gunBody.position.set(0, 0.012, 0.02);
  gunGroup.add(gunBody);

  gunStripe = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.012, 0.22), mint);
  gunStripe.position.set(0.012, 0.036, -0.06);
  gunGroup.add(gunStripe);

  const index = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.02, 0.11), char);
  index.position.set(0.012, 0.018, -0.1);
  gunGroup.add(index);
  const mid = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.018, 0.08), char);
  mid.position.set(-0.012, 0.016, -0.08);
  gunGroup.add(mid);
  const thumb = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.016, 0.05), char);
  thumb.position.set(-0.05, 0.0, 0.02);
  thumb.rotation.y = 0.5;
  gunGroup.add(thumb);

  gunMuzzleLight = new THREE.PointLight(Locker.colors.mintHex, 0, 5);
  gunMuzzleLight.position.set(0.012, 0.03, -0.22);
  gunGroup.add(gunMuzzleLight);

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

  for (let i = 0; i < 10; i++) {
    const g = sableStd(i % 2 ? 0x182218 : 0x1e2a1c, { roughness: 0.96, metalness: 0.02, flatShading: true });
    const strip = new THREE.Mesh(new THREE.PlaneGeometry(26, 2.2), g);
    strip.rotation.x = -Math.PI / 2;
    strip.position.set(0, -1.64, 3.2 - i * 2.2);
    rangeHallGroup.add(strip);
  }

  const mint = new THREE.MeshBasicMaterial({ color: Locker.colors.mintHex });
  const lane = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.02, 20), mint);
  lane.position.set(0, -1.62, -7);
  rangeHallGroup.add(lane);

  const post = sableStd(0x2a241c, { roughness: 0.8 });
  for (const x of [-8.2, 8.2]) {
    for (let i = 0; i < 6; i++) {
      const p = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.08, 2.6, 6), post);
      p.position.set(x, -0.34, 1.5 - i * 3.4);
      rangeHallGroup.add(p);
    }
    const rail = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.07, 18), post);
    rail.position.set(x, 0.72, -7);
    rangeHallGroup.add(rail);
  }

  const net = new THREE.Mesh(
    new THREE.PlaneGeometry(18, 5.2, 16, 5),
    new THREE.MeshBasicMaterial({ color: 0x4a5c50, transparent: true, opacity: 0.28, wireframe: true })
  );
  net.position.set(0, 0.9, -17.1);
  rangeHallGroup.add(net);

  const flood = new THREE.PointLight(0xffe8c8, 1.1, 22, 2);
  flood.position.set(-5, 5.5, -3);
  rangeHallGroup.add(flood);
  const flood2 = flood.clone();
  flood2.position.set(5, 5.5, -9);
  rangeHallGroup.add(flood2);

  buildYardBunkers(rangeHallGroup);
}

function inflateMat(hex) {
  return new THREE.MeshStandardMaterial({
    color: hex, roughness: 0.22, metalness: 0.08, flatShading: false,
  });
}

function addYard(group, mesh, x, y, z, rotY) {
  mesh.position.set(x, y, z);
  if (rotY) mesh.rotation.y = rotY;
  mesh.castShadow = false;
  group.add(mesh);
  return mesh;
}

function sausageX(radius, length, mat) {
  const cyl = Math.max(0.05, length - radius * 2);
  const m = new THREE.Mesh(new THREE.CapsuleGeometry(radius, cyl, 5, 14), mat);
  m.rotation.z = Math.PI / 2;
  return m;
}

function capEnds(group, x, y, z, alongX, radius, capMat) {
  const a = new THREE.Mesh(new THREE.SphereGeometry(radius * 1.02, 12, 10), capMat);
  const b = a.clone();
  a.position.set(x - alongX, y, z);
  b.position.set(x + alongX, y, z);
  group.add(a); group.add(b);
}

function buildYardBunkers(group) {
  const bone = inflateMat(Locker.colors.boneHex);
  const rust = inflateMat(Locker.colors.rustHex);
  const mint = inflateMat(Locker.colors.mintHex);
  const floorY = -1.64;

  const pad = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.1, 1.3), rust);
  addYard(group, pad, 0, floorY + 0.05, 1.35, 0);
  const padLip = new THREE.Mesh(new THREE.BoxGeometry(2.14, 0.03, 1.34), mint);
  addYard(group, padLip, 0, floorY + 0.11, 1.35, 0);

  const tape = new THREE.Mesh(new THREE.BoxGeometry(16.5, 0.06, 0.12), mint);
  addYard(group, tape, 0, floorY + 0.04, -16.5, 0);

  const beamL = sausageX(0.32, 2.6, bone);
  addYard(group, beamL, -3.4, floorY + 0.32, -4.2, 0);
  capEnds(group, -3.4, floorY + 0.32, -4.2, 1.15, 0.32, rust);
  const beamR = sausageX(0.32, 2.6, bone);
  addYard(group, beamR, 3.4, floorY + 0.32, -4.2, 0);
  capEnds(group, 3.4, floorY + 0.32, -4.2, 1.15, 0.32, rust);

  const drum = new THREE.Mesh(new THREE.CapsuleGeometry(0.58, 0.7, 6, 16), rust);
  addYard(group, drum, -1.6, floorY + 0.93, -7.0, 0);
  const drumRing = new THREE.Mesh(new THREE.TorusGeometry(0.6, 0.05, 8, 18), mint);
  drumRing.rotation.x = Math.PI / 2;
  addYard(group, drumRing, -1.6, floorY + 1.55, -7.0, 0);

  const peak = new THREE.Mesh(new THREE.ConeGeometry(0.92, 1.85, 5), bone);
  addYard(group, peak, 2.2, floorY + 0.92, -8.5, 0.35);
  const peakBase = new THREE.Mesh(new THREE.SphereGeometry(0.55, 12, 10), rust);
  addYard(group, peakBase, 2.2, floorY + 0.28, -8.5, 0);

  const stack = new THREE.Mesh(new THREE.CapsuleGeometry(0.72, 0.35, 4, 12), rust);
  stack.scale.set(1.15, 1, 1.15);
  addYard(group, stack, -2.8, floorY + 0.72, -11.0, 0.12);

  const wing = sausageX(0.28, 2.7, bone);
  addYard(group, wing, 0, floorY + 0.3, -12.5, 0);
  const wingStem = new THREE.Mesh(new THREE.CapsuleGeometry(0.28, 0.55, 4, 12), bone);
  addYard(group, wingStem, 0, floorY + 0.7, -12.5, 0);

  const crossA = sausageX(0.28, 2.0, mint);
  addYard(group, crossA, 3.0, floorY + 0.42, -14.0, 0);
  const crossB = new THREE.Mesh(new THREE.CapsuleGeometry(0.28, 1.44, 5, 14), mint);
  crossB.rotation.x = Math.PI / 2;
  addYard(group, crossB, 3.0, floorY + 0.42, -14.0, 0);

  const drumFar = new THREE.Mesh(new THREE.CapsuleGeometry(0.52, 0.55, 5, 14), bone);
  addYard(group, drumFar, -3.2, floorY + 0.8, -14.5, 0);
}

const YARD_PEEKS = [
  [-3.4, -0.7, -3.9],
  [3.4, -0.7, -3.9],
  [-0.5, 0.35, -6.6],
  [2.4, 0.55, -8.1],
  [-2.6, 0.05, -10.5],
  [0.8, -0.15, -12.0],
  [3.1, 0.15, -13.5],
  [-3.0, 0.25, -14.1],
];

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
  const bone = new THREE.MeshStandardMaterial({
    color: Locker.colors.boneHex, roughness: 0.38, metalness: 0.06, flatShading: false,
  });
  const mint = new THREE.MeshStandardMaterial({
    color: Locker.colors.mintHex, emissive: Locker.colors.mintHex, emissiveIntensity: 0.45, roughness: 0.3,
  });
  const fly = kind === "clay" || kind === "rise";
  const plate = new THREE.Mesh(hexPlateGeo(fly ? 0.5 : 0.62, 0.08), bone);
  group.add(plate);
  const core = new THREE.Mesh(hexPlateGeo(fly ? 0.22 : 0.26, 0.1), mint);
  core.position.y = 0.02;
  group.add(core);
  const wire = plate;
  return { group, core, wire };
}

function spawnOrb3D(opts) {
  const o = Object.assign({
    kind: "sit", vx: 0, vy: 0, vz: 0, worth: 100, hue: 165,
    life: 0, born: performance.now(), r: 28,
  }, opts);
  const meshObj = createTargetMesh(o.kind, o.hue);
  o.mesh = meshObj.group;
  o.mesh.userData.orb = o;
  o.mesh.traverse((c) => { c.userData.orb = o; });
  rangeTargetGroup.add(o.mesh);
  S.orbs.push(o);
  return o;
}

function worldToHud(pos) {
  const v = pos.clone().project(camera);
  return { x: (v.x * 0.5 + 0.5) * W, y: (-v.y * 0.5 + 0.5) * H };
}

function shatterTarget3D(pos, hue) {
  const count = 16;
  const col = new THREE.Color(`hsl(${hue}, 100%, 65%)`);
  const shardMat = new THREE.MeshBasicMaterial({
    color: Math.random() < 0.35 ? Locker.colors.mintHex : Locker.colors.boneHex,
  });
  for (let i = 0; i < count; i++) {
    const sGeo = new THREE.TetrahedronGeometry(0.07 + Math.random() * 0.07);
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
function sharedMatch() {
  return !!(S.online && !S.warmup && S.room && S.player);
}

function reportSharedFire(shot, localPlateId) {
  if (!sharedMatch() || !S.room || !S.player) return;
  if (!S.sharedPending) S.sharedPending = new Set();
  if (!S.sharedDead) S.sharedDead = new Set();
  if (localPlateId) S.sharedPending.add(localPlateId);
  const uv = shot && shot.uv ? [shot.uv.x, shot.uv.y] : [S.aim.x / W, S.aim.y / H];
  fetch("/api/lobby/hit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: S.room,
      player: S.player,
      uv: uv,
      lifted: !!(shot && shot.lifted),
      t_hw: shot && shot.t_hw != null ? shot.t_hw : 0,
      fire_ms: performance.now() - S.rangeStart,
      aspect: W / H,
    }),
  }).then(function (res) { return res.json(); }).then(function (data) {
    if (localPlateId && S.sharedPending) S.sharedPending.delete(localPlateId);
    if (!data || !data.ok) return;
    if (data.hit) S.sharedDead.add(data.hit);
    applySharedSim(data);
  }).catch(function () { /* snapshot poll is the authority */ });
}

function spawnSharedPlate(p) {
  const o = spawnOrb3D({
    kind: p.kind,
    worth: p.worth || 100,
    hue: 165,
    id: p.id,
    vx: p.vx || 0,
    vy: p.vy || 0,
    vz: p.vz || 0,
  });
  o.mesh.position.set(p.x, p.y, p.z);
  o.baseY = p.baseY != null ? p.baseY : p.y;
  o.life = typeof p.life === "number" ? p.life : 0;
  if (p.kind === "clay" || p.kind === "rise") pullWhistle();
  return o;
}

function applySharedSim(data) {
  if (!data || !data.ok || data.phase !== "range" || data.seed == null) return;
  if (!rangeTargetGroup) return;
  S.seed = data.seed;
  if (typeof data.elapsed_ms === "number") {
    S.rangeStart = performance.now() - data.elapsed_ms;
  }
  if (!S.sharedDead) S.sharedDead = new Set();
  if (!S.sharedPending) S.sharedPending = new Set();
  const deadList = data.dead || [];
  for (const d of deadList) {
    const id = typeof d === "string" ? d : d.id;
    if (id) S.sharedDead.add(id);
  }
  const live = [];
  for (const p of (data.plates || [])) {
    if (p && p.id && !S.sharedDead.has(p.id) && !S.sharedPending.has(p.id)) live.push(p);
  }
  const liveIds = new Set(live.map((p) => p.id));
  const gone = [];
  for (const o of S.orbs) {
    if (o.id && !liveIds.has(o.id)) gone.push(o);
  }
  for (const o of gone) {
    if (o.mesh) {
      if (S.sharedDead.has(o.id)) shatterTarget3D(o.mesh.position.clone(), o.hue);
      rangeTargetGroup.remove(o.mesh);
    }
  }
  if (gone.length) S.orbs = S.orbs.filter((o) => gone.indexOf(o) < 0);
  for (const p of live) {
    let o = null;
    for (const cur of S.orbs) {
      if (cur.id === p.id) { o = cur; break; }
    }
    if (!o) {
      spawnSharedPlate(p);
      continue;
    }
    if (typeof p.life === "number") o.life = p.life;
    if (o.mesh && (o.kind === "clay" || o.kind === "rise")) {
      o.mesh.position.set(p.x, p.y, p.z);
      o.vx = p.vx;
      o.vy = p.vy;
      o.vz = p.vz;
    }
  }
}

async function pullSharedSim() {
  if (!sharedMatch() || !S.room) return;
  try {
    const res = await fetch("/api/lobby?code=" + encodeURIComponent(S.room));
    const data = await res.json();
    if (data && data.ok) applySharedSim(data);
  } catch (e) { /* next poll */ }
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
  S.sharedDead = new Set();
  S.sharedPending = new Set();
  if (sharedMatch()) {
    pullSharedSim();
    ensureLobbyPoll();
    return;
  }
  const first = spawnOrb3D({ kind: "sit", worth: 100, hue: 165 });
  first.mesh.position.set(0.2, 0.35, -6.6);
  first.baseY = 0.35;
}
function randomOrb(hard) {
  const roll = Math.random();
  let kind = "sit";
  if (roll > 0.42) kind = "clay";
  else if (roll > 0.22) kind = "rise";
  const worth = kind === "clay" ? 250 : (kind === "rise" ? 180 : 100);
  const o = spawnOrb3D({ kind, worth, hue: 165 });
  const p = YARD_PEEKS[(Math.random() * YARD_PEEKS.length) | 0];
  if (kind === "clay") {
    const left = Math.random() < 0.5;
    o.mesh.position.set(left ? -8.5 : 8.5, 0.7 + Math.random() * 0.7, -5 - Math.random() * 8);
    o.vx = (left ? 1 : -1) * (4.2 + Math.random() * (hard ? 5 : 2.2));
    o.vy = 1.4 + Math.random();
    o.vz = -0.8 - Math.random();
    pullWhistle();
  } else if (kind === "rise") {
    o.mesh.position.set(p[0], -1.45, p[2]);
    o.vy = 3.4 + Math.random() * 1.4;
    pullWhistle();
  } else {
    o.mesh.position.set(p[0], p[1], p[2]);
    o.baseY = p[1];
  }
  return o;
}

function popup(x, y, text, hue) {
  S.pops.push({ x, y, text, hue, age: 0, life: 0.7 });
}

function desiredOrbCount(elapsed) {
  if (elapsed < 1800) return 1;
  if (elapsed < 14000) return 2;
  if (elapsed < 32000) return 3;
  return 4;
}

function updateRange(dt, now) {
  const elapsed = now - S.rangeStart;
  if (elapsed >= RANGE_MS) { setPhase("results"); return; }
  const shared = sharedMatch();
  if (!shared) {
    const want = desiredOrbCount(elapsed);
    const hard = elapsed > 35000;
    while (S.orbs.length < want && (elapsed >= 2000 || S.orbs.length === 0)) randomOrb(hard);
  }

  const gone = [];
  for (const o of S.orbs) {
    o.life += dt;
    if (!o.mesh) continue;
    if (o.kind === "clay" || o.kind === "rise") {
      o.mesh.position.x += o.vx * dt;
      o.mesh.position.y += o.vy * dt;
      o.mesh.position.z += (o.vz || 0) * dt;
      o.vy -= 4.6 * dt;
      const p = o.mesh.position;
      if (!shared && (p.y < -1.7 || p.x < -10 || p.x > 10 || p.z < -18 || p.z > 3 || o.life >= PLATE_MAX_LIFE_S)) gone.push(o);
    } else if (o.kind === "sit") {
      if (o.baseY == null) o.baseY = o.mesh.position.y;
      if (o.phase == null) o.phase = 0;
      if (o.life >= SIT_DWELL_S) {
        o.mesh.position.y += SIT_DROP_VY * dt;
        if (!shared && (o.mesh.position.y < -1.7 || o.life >= PLATE_MAX_LIFE_S)) gone.push(o);
      } else {
        o.phase += dt * 1.6;
        o.mesh.position.y = o.baseY + Math.sin(o.phase) * 0.07;
      }
    }
    if (gone.indexOf(o) < 0) {
      o.mesh.lookAt(camera.position);
      if (o.kind === "clay") o.mesh.rotateZ(3.2 * dt);
    }
  }
  for (const o of gone) {
    missTick();
    S.combo = 0;
    if (o.mesh) {
      const hud = worldToHud(o.mesh.position);
      popup(hud.x, hud.y, "ESC", 20);
      rangeTargetGroup.remove(o.mesh);
    }
  }
  if (gone.length) S.orbs = S.orbs.filter((o) => gone.indexOf(o) < 0);

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

export {
  OP_CANCHO,
  STYLE_DEFAULT,
  STYLE_RANKED,
  STYLE_NIGHT,
  Locker,
  RANGE_MS,
  SIT_DWELL_S,
  SIT_DROP_VY,
  PLATE_MAX_LIFE_S,
  HUD_PAD,
  Bay,
  speak,
  unlockAudio,
  bang,
  hitBlip,
  missTick,
  pullWhistle,
  YARD_PEEKS,
  init3D,
  fireBay3D,
  createTargetMesh,
  spawnOrb3D,
  worldToHud,
  shatterTarget3D,
  addBulletTracer,
  sharedMatch,
  reportSharedFire,
  spawnSharedPlate,
  applySharedSim,
  pullSharedSim,
  startRange,
  randomOrb,
  popup,
  desiredOrbCount,
  updateRange,
  tickBay,
};
