/* SABLE — house.js
   Salt House gallery (60s plates/clays), shared match hooks, Bay.
   Sit / flyer pose is closed-form from life (sitPoseY / flyerPose) —
   same house local and rewind. Do not Euler-integrate flyers.
   Hitscan is the same sphere as lobby rewind (hitscanRange / plateRadius).
   Do not mesh-test the spun hex — a HID peek that hits the plate can
   miss the room sphere (and the reverse).
   SablePort look/mode seam: original house / Yard / Bay. Look bible stays
   charcoal / bone / mint / rust. Feeling notes: docs/port.md.
   Trackpad / HID click fires from the AimBus mailbox — never waits on camera. */

import * as THREE from "./vendor/three.module.js";
import { S, W, H, dpr, phase, aimBus, clamp, assignHangar } from "./aim.js";
import { $, canvas3D, setPhase, ensureLobbyPoll } from "./boot.js";
import {
  unlockAudio,
  bang,
  hitBlip,
  missTick,
  pullWhistle,
  liftMint,
  mintTell,
  SABLE_AUDIO_MINT_TELL,
} from "./audio.js";

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
      lift: SABLE_AUDIO_MINT_TELL,
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
    applyLockerLook();
    return this.equippedStyle;
  }
};

const RANGE_MS = 60000;
const SIT_DWELL_S = 4.2;
const SIT_DROP_VY = -3.2;
const SIT_BOB_RATE = 1.6;
const SIT_BOB_AMP = 0.07;
const GRAVITY = 4.6;
const PLATE_MAX_LIFE_S = 7.5;
const CAM_EYE = { x: 0, y: 1.64, z: 2.05 };
const CAM_AT = { x: 0, y: 0.55, z: -12 };
const CAM_UP = { x: 0, y: 1, z: 0 };
const FOV_Y_DEG = 62;
const DEFAULT_ASPECT = 1280 / 720;

function sitPoseY(baseY, life) {
  // Closed-form sit pose from life. Same formula as lobby.sit_pose_y.
  // Local practice (Offline / WARM UP / wait_practice) and match_live rewind
  // share this house. Do not accumulate an unsynced phase — friends would split.
  if (life >= SIT_DWELL_S) return baseY + SIT_DROP_VY * (life - SIT_DWELL_S);
  return baseY + Math.sin(life * SIT_BOB_RATE) * SIT_BOB_AMP;
}

function flyerPose(x0, y0, z0, vx0, vy0, vz0, life) {
  // Closed-form flyer pose from life. Same formula as lobby.flyer_pose.
  // Euler (y += vy*dt; vy -= g*dt) drifts ~0.5*g*dt*t vs rewind — a HID
  // peek that hits the mesh can miss the room sphere (and the reverse).
  return {
    x: x0 + vx0 * life,
    y: y0 + vy0 * life - 0.5 * GRAVITY * life * life,
    z: z0 + vz0 * life,
    vx: vx0,
    vy: vy0 - GRAVITY * life,
    vz: vz0,
  };
}

function bindFlyerBirth(o) {
  if (!o || !o.mesh) return;
  o.x0 = o.mesh.position.x;
  o.y0 = o.mesh.position.y;
  o.z0 = o.mesh.position.z;
  o.vx0 = o.vx || 0;
  o.vy0 = o.vy || 0;
  o.vz0 = o.vz || 0;
}

function plateRadius(kind) {
  // Same house as lobby._plate_radius. Hex mesh is Look only.
  return kind === "clay" || kind === "rise" ? 0.50 : 0.62;
}

function _vsub(a, b) { return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z }; }
function _vadd(a, b) { return { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z }; }
function _vmul(a, s) { return { x: a.x * s, y: a.y * s, z: a.z * s }; }
function _vdot(a, b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
function _vcross(a, b) {
  return { x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x };
}
function _vnorm(a) {
  const len = Math.sqrt(_vdot(a, a)) || 1;
  return _vmul(a, 1 / len);
}

function rayFromUv(uvx, uvy, aspect) {
  // World ray from last-committed UV. Same 62° yard camera as lobby.ray_from_uv.
  // Does not invent pose. Does not read the THREE camera matrix on the click.
  const ndcX = uvx * 2 - 1;
  const ndcY = 1 - uvy * 2;
  const tanH = Math.tan((FOV_Y_DEG * Math.PI / 180) * 0.5);
  const asp = aspect && aspect > 0.2 ? aspect : DEFAULT_ASPECT;
  const zAxis = _vnorm(_vsub(CAM_EYE, CAM_AT));
  const xAxis = _vnorm(_vcross(CAM_UP, zAxis));
  const yAxis = _vcross(zAxis, xAxis);
  const local = { x: ndcX * tanH * asp, y: ndcY * tanH, z: -1 };
  const world = _vadd(_vadd(_vmul(xAxis, local.x), _vmul(yAxis, local.y)), _vmul(zAxis, local.z));
  return { origin: { x: CAM_EYE.x, y: CAM_EYE.y, z: CAM_EYE.z }, direction: _vnorm(world) };
}

function raySphere(origin, direction, center, radius) {
  const oc = _vsub(origin, center);
  const b = 2 * _vdot(oc, direction);
  const c = _vdot(oc, oc) - radius * radius;
  const disc = b * b - 4 * c;
  if (disc < 0) return null;
  const t = (-b - Math.sqrt(disc)) * 0.5;
  if (t <= 0) return null;
  return t;
}

function hitscanRange(uvx, uvy, aspect) {
  // Peeked UV vs last committed plate pose. Same sphere as lobby._hitscan.
  // Fire calls this — it is not a net/cam/sim wait.
  const ray = rayFromUv(uvx, uvy, aspect);
  let best = null;
  let bestT = Infinity;
  for (const o of S.orbs) {
    if (!o || !o.mesh) continue;
    const p = o.mesh.position;
    const t = raySphere(ray.origin, ray.direction, { x: p.x, y: p.y, z: p.z }, plateRadius(o.kind));
    if (t != null && t < bestT) {
      bestT = t;
      best = o;
    }
  }
  const far = best ? bestT : 20;
  return {
    hit: best,
    t: best ? bestT : null,
    point: {
      x: ray.origin.x + ray.direction.x * far,
      y: ray.origin.y + ray.direction.y * far,
      z: ray.origin.z + ray.direction.z * far,
    },
    origin: ray.origin,
    direction: ray.direction,
  };
}

function bindFlyerBirthFromPlate(o, p) {
  if (!o || !p) return;
  if (p.x0 != null && p.y0 != null && p.z0 != null) {
    o.x0 = p.x0;
    o.y0 = p.y0;
    o.z0 = p.z0;
    o.vx0 = p.vx0 != null ? p.vx0 : (p.vx || 0);
    o.vy0 = p.vy0 != null ? p.vy0 : (p.vy || 0);
    o.vz0 = p.vz0 != null ? p.vz0 : (p.vz || 0);
    return;
  }
  const life = typeof p.life === "number" ? p.life : 0;
  const vx = p.vx || 0;
  const vy = p.vy || 0;
  const vz = p.vz || 0;
  o.vx0 = vx;
  o.vz0 = vz;
  o.vy0 = vy + GRAVITY * life;
  o.x0 = p.x - vx * life;
  o.z0 = p.z - vz * life;
  o.y0 = p.y - vy * life - 0.5 * GRAVITY * life * life;
}

const HUD_PAD = 16;

// --- Bay 1v1 — original booth (docs/maps/bay.md). Not a third-party map. ---
const BAY_TO_WIN = 5;
const BAY_SPEED = 4.2;
const BAY_EXPOSE_S = 0.12;
const BAY_FREEZE_PAD_S = 0.45;
const BAY_FOE_RADIUS = 0.46;
const BAY_SPAWN_A = { x: 0, y: 1.64, z: 10 };
const BAY_SPAWN_B = { x: 0, y: 0.89, z: -10 };

function bayInLeftWindow(x, z) {
  return x > -7.5 && x < -4.8 && z > 2.4 && z < 5.6;
}
function bayInRightAngle(x, z) {
  return x > 4.6 && x < 7.5 && z > 1.6 && z < 5.8;
}
function bayInOpenMiddle(x, z) {
  if (bayInLeftWindow(x, z) || bayInRightAngle(x, z)) return false;
  return z <= 0.65 && z > -12.5 && Math.abs(x) < 7.6;
}
function bayStallHit(x, z) {
  return Math.abs(x) < 2.15 && z > -0.55 && z < 0.55;
}
function bayCoverChip(x, z, lifted, frozen, over) {
  if (over || frozen) return "DROP";
  if (bayInOpenMiddle(x, z)) return "OPEN";
  if (bayInLeftWindow(x, z)) return "WINDOW";
  if (bayInRightAngle(x, z)) return "ANGLE";
  return lifted ? "GUN" : "PAD";
}

const Bay = {
  active: false,
  you: 0,
  them: 0,
  toWin: BAY_TO_WIN,
  round: 1,
  speed: BAY_SPEED,
  seat: "A",
  pos: { x: BAY_SPAWN_A.x, y: BAY_SPAWN_A.y, z: BAY_SPAWN_A.z },
  foe: {
    x: BAY_SPAWN_B.x, y: BAY_SPAWN_B.y, z: BAY_SPAWN_B.z,
    radius: BAY_FOE_RADIUS, alive: true, strafeT: 0,
  },
  frozen: false,
  freezeT: 0,
  freezePadS: BAY_FREEZE_PAD_S,
  expose: 0,
  exposeMax: BAY_EXPOSE_S,
  voText: "",
  voT: 0,
  missT: 0,
  over: false,
  fireMs: 0,
  wasLifted: false,
  keys: { w: false, a: false, s: false, d: false },
  resetRound() {
    const spawn = this.seat === "B" ? BAY_SPAWN_B : BAY_SPAWN_A;
    const foeSpawn = this.seat === "B" ? BAY_SPAWN_A : BAY_SPAWN_B;
    this.pos.x = spawn.x;
    this.pos.y = BAY_SPAWN_A.y;
    this.pos.z = spawn.z;
    this.foe.x = foeSpawn.x;
    this.foe.y = BAY_SPAWN_B.y;
    this.foe.z = foeSpawn.z;
    this.foe.alive = true;
    this.foe.strafeT = 0;
    this.expose = 0;
    this.frozen = false;
  },
  resetMatch() {
    this.you = 0;
    this.them = 0;
    this.round = 1;
    this.over = false;
    this.fireMs = 0;
    this.resetRound();
  },
  vo(line) {
    this.voText = line;
    this.voT = 0.9;
    // Mint-tell is the oscillator chirp (afterLiftState). No browser TTS.
    if (line !== SABLE_AUDIO_MINT_TELL) speak(line);
  }
};

let liftTellArmed = false;

function afterLiftState() {
  const lifted = !!(S.lifted || S.desktop || S.forceGun);
  const live = phase === "range" || phase === "bay" || phase === "calibrate" || phase === "lock";
  if (live && lifted && !liftTellArmed) mintTell();
  if (live) liftTellArmed = lifted;
  if (!live) liftTellArmed = false;
}

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
// ==========================================
// --- Three.js 3D Engine Architecture ---
// ==========================================
export let renderer, scene, camera;
export let gunGroup, gunBody, gunStripe, gunMuzzleLight, gunCuff;
export let rangeTargetGroup, rangeHallGroup, shardGroup;
export let bayGroup, foeGroup, foeMesh, foeVisor, foeStripe, foeCollar, foeChest, foeWrist;
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
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.toneMappingExposure = 1.0;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0c10);
  scene.fog = new THREE.FogExp2(0x101214, 0.022);

  camera = new THREE.PerspectiveCamera(62, W / H, 0.08, 160);
  camera.position.set(0, 1.64, 2.05);
  camera.lookAt(0, 0.55, -12);

  scene.add(new THREE.HemisphereLight(Locker.colors.boneHex, 0x101214, 0.55));
  const dir = new THREE.DirectionalLight(Locker.colors.boneHex, 0.35);
  dir.position.set(-6, 16, 4);
  scene.add(dir);

  buildFirstPersonGun();
  buildRange3D();
  buildBay3D();
}

function bayUnshaded(hex) {
  return new THREE.MeshBasicMaterial({ color: hex });
}

function sableStd(hex, extra) {
  void extra;
  return bayUnshaded(hex);
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
  const bone = bayUnshaded(Locker.colors.boneHex);
  const rust = bayUnshaded(Locker.colors.rustHex);
  const char = bayUnshaded(Locker.colors.bodyHex);
  const mint = bayUnshaded(Locker.colors.mintHex);

  gunCuff = new THREE.Mesh(new THREE.CylinderGeometry(0.046, 0.05, 0.07, 8), rust);
  gunCuff.rotation.x = Math.PI / 2;
  gunCuff.position.set(0, -0.01, 0.1);
  gunGroup.add(gunCuff);

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

function addBarrelRib(group, z, charMat, rustMat) {
  const r = 5.45;
  const rustR = 5.12;
  const rib = new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(-r, -1.64, z),
    new THREE.Vector3(0, -1.64 + r, z),
    new THREE.Vector3(r, -1.64, z)
  );
  const rustEdge = new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(-rustR, -1.64, z),
    new THREE.Vector3(0, -1.64 + rustR, z),
    new THREE.Vector3(rustR, -1.64, z)
  );
  group.add(new THREE.Mesh(new THREE.TubeGeometry(rib, 28, 0.16, 8, false), charMat));
  group.add(new THREE.Mesh(new THREE.TubeGeometry(rustEdge, 28, 0.055, 6, false), rustMat));
}

function buildRange3D() {
  rangeHallGroup = new THREE.Group();
  rangeTargetGroup = new THREE.Group();
  shardGroup = new THREE.Group();
  scene.add(rangeHallGroup);
  scene.add(rangeTargetGroup);
  scene.add(shardGroup);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(14, 22),
    bayUnshaded(0x10141a)
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -1.64, -7);
  rangeHallGroup.add(floor);

  const mint = bayUnshaded(Locker.colors.mintHex);
  const lane = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.03, 20), mint);
  lane.position.set(0, -1.62, -7);
  rangeHallGroup.add(lane);

  const vaultMat = bayUnshaded(Locker.colors.bodyHex);
  vaultMat.side = THREE.DoubleSide;
  const vault = new THREE.Mesh(
    new THREE.CylinderGeometry(5.6, 5.6, 21, 32, 1, true, Math.PI * 0.5, Math.PI),
    vaultMat
  );
  vault.rotation.x = Math.PI / 2;
  vault.position.set(0, -1.64, -7);
  rangeHallGroup.add(vault);

  const ribChar = bayUnshaded(0x1a222c);
  const ribRust = bayUnshaded(Locker.colors.rustHex);
  const ribZ = [-0.4, -4.2, -8.0, -11.8, -15.4];
  for (const z of ribZ) addBarrelRib(rangeHallGroup, z, ribChar, ribRust);

  const post = bayUnshaded(Locker.colors.bodyHex);
  for (const z of [-0.4, -15.4]) {
    for (const x of [-5.5, 5.5]) {
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.22, 2.2, 0.22), post);
      p.position.set(x, -0.54, z);
      rangeHallGroup.add(p);
    }
  }

  const backstop = new THREE.Mesh(new THREE.BoxGeometry(6.4, 2.4, 1.35), ribRust);
  backstop.position.set(0, -0.44, -16.8);
  rangeHallGroup.add(backstop);

  buildYardBunkers(rangeHallGroup);
}

function inflateMat(hex) {
  return bayUnshaded(hex);
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
  // Charcoal mass + rust rim. Bone is reserved for plates so silhouettes stay readable.
  const charcoal = inflateMat(0x1a222c);
  const rust = inflateMat(Locker.colors.rustHex);
  const floorY = -1.64;

  const pad = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.12, 1.3), rust);
  addYard(group, pad, 0, floorY + 0.06, 1.35, 0);

  const beamL = sausageX(0.38, 2.8, charcoal);
  addYard(group, beamL, -3.4, floorY + 0.38, -4.2, 0);
  capEnds(group, -3.4, floorY + 0.38, -4.2, 1.2, 0.38, rust);
  const beamR = sausageX(0.38, 2.8, charcoal);
  addYard(group, beamR, 3.4, floorY + 0.38, -4.2, 0);
  capEnds(group, 3.4, floorY + 0.38, -4.2, 1.2, 0.38, rust);

  const drum = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.7, 1.2), rust);
  addYard(group, drum, -1.6, floorY + 0.35, -7.0, 0);

  const peak = new THREE.Mesh(new THREE.ConeGeometry(0.98, 0.92, 5), charcoal);
  addYard(group, peak, 2.2, floorY + 0.46, -8.5, 0.35);
  const peakRim = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.72, 0.08, 5), rust);
  addYard(group, peakRim, 2.2, floorY + 0.04, -8.5, 0.35);
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

function applyLockerLook() {
  const id = Locker.equippedStyle;
  let body = Locker.colors.bodyHex;
  let rust = Locker.colors.rustHex;
  let stripe = Locker.colors.mintHex;
  if (id === STYLE_RANKED) {
    body = 0x0a0d12;
    rust = 0x734234;
  } else if (id === STYLE_NIGHT) {
    body = 0x050508;
    rust = 0x331a14;
    stripe = S.lifted ? Locker.colors.mintHex : 0x1e5947;
  }
  if (gunStripe && gunStripe.material && gunStripe.material.color) {
    gunStripe.material.color.setHex(stripe);
  }
  if (gunCuff && gunCuff.material && gunCuff.material.color) {
    gunCuff.material.color.setHex(rust);
  }
  if (foeWrist && foeWrist.material && foeWrist.material.color) {
    foeWrist.material.color.setHex(rust);
  }
  if (foeMesh && foeMesh.material && foeMesh.material.color) {
    foeMesh.material.color.setHex(body);
  }
  if (foeCollar && foeCollar.material && foeCollar.material.color) {
    foeCollar.material.color.setHex(body);
  }
  if (foeStripe && foeStripe.material && foeStripe.material.color) {
    foeStripe.material.color.setHex(stripe);
  }
  if (foeChest) {
    foeChest.visible = id === STYLE_RANKED;
    if (foeChest.material && foeChest.material.color) {
      foeChest.material.color.setHex(Locker.colors.mintHex);
    }
  }
}

function buildBay3D() {
  bayGroup = new THREE.Group();
  bayGroup.visible = false;
  scene.add(bayGroup);

  const charcoal = bayUnshaded(0x101214);
  const wallMat = bayUnshaded(0x0c0d10);
  const stallMat = bayUnshaded(0x2a2c28);
  const rustMat = bayUnshaded(Locker.colors.rustHex);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(16, 28), charcoal);
  floor.rotation.x = -Math.PI / 2;
  bayGroup.add(floor);

  const wallH = 4.2;
  const wallL = new THREE.Mesh(new THREE.BoxGeometry(0.2, wallH, 28), wallMat);
  wallL.position.set(-8, wallH * 0.5, 0);
  const wallR = wallL.clone();
  wallR.position.x = 8;
  const wallN = new THREE.Mesh(new THREE.BoxGeometry(16, wallH, 0.2), wallMat);
  wallN.position.set(0, wallH * 0.5, 14);
  const wallS = wallN.clone();
  wallS.position.z = -14;
  bayGroup.add(wallL);
  bayGroup.add(wallR);
  bayGroup.add(wallN);
  bayGroup.add(wallS);

  const stall = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.84, 1.1), stallMat);
  stall.position.set(0, 0.42, 0);
  bayGroup.add(stall);

  const chipGeo = new THREE.BoxGeometry(2.4, 1.1, 0.7);
  const leftChip = new THREE.Mesh(chipGeo, rustMat);
  leftChip.position.set(-6.15, 0.55, 4.0);
  const rightChip = new THREE.Mesh(chipGeo, rustMat);
  rightChip.position.set(6.05, 0.55, 3.7);
  bayGroup.add(leftChip);
  bayGroup.add(rightChip);

  foeGroup = new THREE.Group();
  foeMesh = new THREE.Mesh(new THREE.CapsuleGeometry(0.28, 1.22, 4, 8), bayUnshaded(Locker.colors.bodyHex));
  foeMesh.position.y = 0.89;
  foeGroup.add(foeMesh);

  foeCollar = new THREE.Mesh(new THREE.CylinderGeometry(0.30, 0.32, 0.16, 8), bayUnshaded(Locker.colors.bodyHex));
  foeCollar.position.y = 1.52;
  foeGroup.add(foeCollar);

  foeStripe = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.10, 0.28), bayUnshaded(Locker.colors.mintHex));
  foeStripe.position.set(0.28, 1.12, 0.12);
  foeGroup.add(foeStripe);
  foeVisor = foeStripe;

  foeWrist = new THREE.Mesh(new THREE.CylinderGeometry(0.055, 0.06, 0.07, 8), bayUnshaded(Locker.colors.rustHex));
  foeWrist.rotation.z = Math.PI / 2;
  foeWrist.position.set(0.28, 1.02, 0.08);
  foeGroup.add(foeWrist);

  foeChest = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.08, 0.12), bayUnshaded(Locker.colors.mintHex));
  foeChest.position.set(0, 1.18, 0.22);
  foeChest.visible = false;
  foeGroup.add(foeChest);

  foeGroup.position.set(BAY_SPAWN_B.x, 0, BAY_SPAWN_B.z);
  bayGroup.add(foeGroup);
}

// --- 3D Target Spawn & Shatter ---
function createTargetMesh(kind, hue) {
  const group = new THREE.Group();
  const bone = bayUnshaded(Locker.colors.boneHex);
  const mint = bayUnshaded(Locker.colors.mintHex);
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
  void hue;
  const count = 16;
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
function rayHitsBayFoe(origin, direction) {
  if (!Bay.foe.alive) return false;
  const cx = Bay.foe.x;
  const cy = 0.89;
  const cz = Bay.foe.z;
  const r = Bay.foe.radius;
  const ox = origin.x - cx;
  const oy = origin.y - cy;
  const oz = origin.z - cz;
  const b = 2 * (ox * direction.x + oy * direction.y + oz * direction.z);
  const c = ox * ox + oy * oy + oz * oz - r * r;
  const disc = b * b - 4 * c;
  if (disc < 0) return false;
  const t = (-b - Math.sqrt(disc)) * 0.5;
  return t > 0;
}

function fireBay3D(raycaster) {
  // HID peek already happened. Stamp the last committed 128 Hz tick — not present.
  // Sphere only. Look tracers peek muzzle after markHid — not a fire gate.
  Bay.fireMs = committedSimMs();
  if (Bay.frozen || Bay.over) { missTick(); return null; }

  const origin = raycaster.ray.origin;
  const dir = raycaster.ray.direction;
  if (rayHitsBayFoe(origin, dir)) {
    const hitPt = new THREE.Vector3(Bay.foe.x, 0.89, Bay.foe.z);
    Bay.you++;
    Bay.foe.alive = false;
    if (foeGroup) foeGroup.visible = false;
    Bay.vo(Locker.operator.vo.hit);
    hitBlip(Bay.you, hitPt.x);
    S.hitstop = 1;
    shatterTarget3D(hitPt, 160);

    Bay.frozen = true;
    Bay.freezeT = 0;
    if (Bay.you >= Bay.toWin) {
      Bay.over = true;
      Bay.vo(Locker.operator.vo.win);
    }
    return hitPt;
  }
  const farPt = origin.clone().add(dir.clone().multiplyScalar(24));
  missTick(farPt.x);
  Bay.missT = 0.06;
  return farPt;
}
function sharedMatch() {
  return !!(S.online && !S.warmup && !S.waitingYard && S.room && S.player && !S.bayMatch);
}

function sharedBay() {
  return !!(S.online && !S.warmup && S.room && S.player && S.bayMatch);
}

function bayLookZ() {
  return Bay.seat === "B" ? Bay.pos.z + 16 : Bay.pos.z - 16;
}

function committedSimMs() {
  return (S.simTick || 0) * (1000 / (S.simHz || 128));
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
      fire_ms: committedSimMs(),
      aspect: W / H,
    }),
  }).then(function (res) { return res.json(); }).then(function (data) {
    if (localPlateId && S.sharedPending) S.sharedPending.delete(localPlateId);
    if (!data || !data.ok) return;
    if (data.hit) S.sharedDead.add(data.hit);
    applySharedSim(data);
  }).catch(function () { /* snapshot poll is the authority */ });
}

function reportSharedBayFire(shot, expose) {
  if (!sharedBay() || !S.room || !S.player) return;
  const uv = shot && shot.uv ? [shot.uv.x, shot.uv.y] : [S.aim.x / W, S.aim.y / H];
  fetch("/api/lobby/hit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: S.room,
      player: S.player,
      uv: expose ? undefined : uv,
      lifted: !!(shot && shot.lifted),
      t_hw: shot && shot.t_hw != null ? shot.t_hw : 0,
      fire_ms: committedSimMs(),
      aspect: W / H,
      pose: { x: Bay.pos.x, z: Bay.pos.z },
      expose: !!expose,
    }),
  }).then(function (res) { return res.json(); }).then(function (data) {
    if (data && data.ok) applySharedBay(data);
  }).catch(function () { /* snapshot poll is the authority */ });
}

function reportSharedBayPose() {
  if (!sharedBay() || !S.room || !S.player) return;
  fetch("/api/lobby/pose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: S.room,
      player: S.player,
      x: Bay.pos.x,
      z: Bay.pos.z,
      fire_ms: committedSimMs(),
    }),
  }).then(function (res) { return res.json(); }).then(function (data) {
    if (data && data.ok) applySharedBay(data);
  }).catch(function () { /* next poll */ });
}

function applySharedBay(data) {
  if (!data || !data.ok || data.phase !== "bay") return;
  S.bayMatch = true;
  if (typeof data.elapsed_ms === "number") {
    S.simTick = Math.floor(data.elapsed_ms * (S.simHz || 128) / 1000);
  }
  const seats = data.seats || {};
  if (S.player && seats[S.player]) {
    Bay.seat = seats[S.player];
    S.baySeat = Bay.seat;
  }
  const scores = data.scores || {};
  let foeId = "";
  for (const id of Object.keys(seats)) {
    if (id !== S.player) { foeId = id; break; }
  }
  S.bayFoe = foeId;
  const poses = data.poses || {};
  if (foeId && poses[foeId]) {
    Bay.foe.x = poses[foeId].x;
    Bay.foe.z = poses[foeId].z;
    if (foeGroup) foeGroup.position.set(Bay.foe.x, 0, Bay.foe.z);
  }
  if (!foeId) return;
  const you = S.player && scores[S.player] != null ? scores[S.player] : Bay.you;
  const them = scores[foeId] != null ? scores[foeId] : Bay.them;
  const scored = you !== Bay.you || them !== Bay.them;
  Bay.you = you;
  Bay.them = them;
  if (typeof data.round === "number") Bay.round = data.round;
  if (data.over) {
    Bay.over = true;
    Bay.frozen = true;
  }
  if (scored && !Bay.over) {
    Bay.frozen = true;
    Bay.freezeT = 0;
    Bay.foe.alive = false;
    if (foeGroup) foeGroup.visible = false;
  }
}

async function pullSharedBay() {
  if (!sharedBay() || !S.room) return;
  try {
    const res = await fetch("/api/lobby?code=" + encodeURIComponent(S.room));
    const data = await res.json();
    if (data && data.ok) applySharedBay(data);
  } catch (e) { /* next poll */ }
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
  bindFlyerBirthFromPlate(o, p);
  return o;
}

function applySharedSim(data) {
  if (!data || !data.ok || data.phase !== "range" || data.seed == null) return;
  if (!rangeTargetGroup) return;
  S.seed = data.seed;
  if (typeof data.elapsed_ms === "number") {
    S.rangeStart = performance.now() - data.elapsed_ms;
    S.simTick = Math.floor(data.elapsed_ms * (S.simHz || 128) / 1000);
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
    if (p.baseY != null) o.baseY = p.baseY;
    // Room pose is authority for sit and flyers. Do not Euler locally.
    bindFlyerBirthFromPlate(o, p);
    if (o.mesh) o.mesh.position.set(p.x, p.y, p.z);
    if (o.kind === "clay" || o.kind === "rise") {
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
function restoreYardLook() {
  Bay.active = false;
  if (scene) {
    scene.background = new THREE.Color(0x0a0c10);
    scene.fog = new THREE.FogExp2(0x101214, 0.022);
  }
  if (camera) {
    camera.position.set(0, 1.64, 2.05);
    camera.lookAt(0, 0.55, -12);
  }
  if (gunGroup) gunGroup.visible = true;
  if (rangeHallGroup) rangeHallGroup.visible = true;
  if (bayGroup) bayGroup.visible = false;
}

function startBay() {
  S.waitingYard = false;
  S.simTick = 0;
  Bay.fireMs = 0;
  Bay.active = true;
  Bay.seat = S.baySeat === "B" ? "B" : "A";
  Bay.resetMatch();
  if (rangeTargetGroup) rangeTargetGroup.visible = false;
  if (rangeHallGroup) rangeHallGroup.visible = false;
  if (bayGroup) bayGroup.visible = true;
  if (foeGroup) foeGroup.visible = true;
  if (scene) {
    scene.background = new THREE.Color(0x0a0c10);
    scene.fog = null;
  }
  if (camera) {
    camera.position.set(Bay.pos.x, Bay.pos.y, Bay.pos.z);
    camera.lookAt(Bay.pos.x, 0.89, bayLookZ());
  }
  if (gunGroup) gunGroup.visible = true;
  applyLockerLook();
  if (sharedBay()) {
    pullSharedBay();
    ensureLobbyPoll();
  }
}

function startWaitingYard() {
  // Waiting-arena always-practice: local Yard plates, no 60s lock, no net.
  S.waitingYard = true;
  S.warmup = false;
  assignHangar("wait_practice");
  S.enteringRange = false;
  restoreYardLook();
  if (rangeTargetGroup) rangeTargetGroup.visible = true;
  if (rangeHallGroup) rangeHallGroup.visible = true;
  if (bayGroup) bayGroup.visible = false;
  while (rangeTargetGroup && rangeTargetGroup.children.length > 0) {
    rangeTargetGroup.remove(rangeTargetGroup.children[0]);
  }
  S.orbs = []; S.parts = []; S.pops = [];
  S.score = 0; S.hits = 0; S.shots = 0; S.combo = 0; S.comboMax = 0;
  S.rangeStart = performance.now();
  S.simTick = 0;
  S.recoil = 0; S.punch = 0; S.flash = 0;
  S.sharedDead = new Set();
  S.sharedPending = new Set();
  const first = spawnOrb3D({ kind: "sit", worth: 100, hue: 165 });
  first.mesh.position.set(0.2, 0.35, -6.6);
  first.baseY = 0.35;
}

function startRange() {
  S.waitingYard = false;
  if (S.warmup) assignHangar("wait_practice");
  else if (S.online && S.room && S.player && !S.bayMatch) assignHangar("match_live");
  else assignHangar("hangar");
  restoreYardLook();
  S.enteringRange = false;
  while (rangeTargetGroup && rangeTargetGroup.children.length > 0) {
    rangeTargetGroup.remove(rangeTargetGroup.children[0]);
  }
  S.orbs = []; S.parts = []; S.pops = [];
  S.score = 0; S.hits = 0; S.shots = 0; S.combo = 0; S.comboMax = 0;
  S.rangeStart = performance.now();
  S.simTick = 0;
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
  } else if (kind === "rise") {
    o.mesh.position.set(p[0], -1.45, p[2]);
    o.vy = 3.4 + Math.random() * 1.4;
  } else {
    o.mesh.position.set(p[0], p[1], p[2]);
    o.baseY = p[1];
  }
  bindFlyerBirth(o);
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

function galleryOver(elapsedMs) {
  return elapsedMs >= RANGE_MS;
}

function galleryLeftMs(elapsedMs) {
  return Math.max(0, RANGE_MS - elapsedMs);
}

function gallerySessionLabel() {
  if (S.warmup) return "WARM UP  " + S.room;
  if (sharedMatch()) return "SHARED  " + S.room;
  if (!S.online) return "GALLERY";
  if (S.playlist === "5v5") return "5v5  " + S.room;
  return "GALLERY  " + S.room;
}

function bayOver() {
  return !!(Bay.over || Bay.you >= Bay.toWin || Bay.them >= Bay.toWin);
}

function baySessionLabel() {
  if (bayOver()) return "MATCH";
  return "FIRST TO 5";
}

function updateRange(dt, elapsed) {
  // dt + elapsed are the 128 Hz sim clock. Render does not own plates.
  if (!S.waitingYard && galleryOver(elapsed)) { setPhase("results"); return; }
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
      if (o.x0 == null) bindFlyerBirth(o);
      const pose = flyerPose(o.x0, o.y0, o.z0, o.vx0, o.vy0, o.vz0, o.life);
      o.mesh.position.set(pose.x, pose.y, pose.z);
      o.vx = pose.vx;
      o.vy = pose.vy;
      o.vz = pose.vz;
      const p = o.mesh.position;
      if (!shared && (p.y < -1.7 || p.x < -10 || p.x > 10 || p.z < -18 || p.z > 3 || o.life >= PLATE_MAX_LIFE_S)) gone.push(o);
    } else if (o.kind === "sit") {
      if (o.baseY == null) o.baseY = o.mesh.position.y;
      o.mesh.position.y = sitPoseY(o.baseY, o.life);
      if (!shared && (o.mesh.position.y < -1.7 || o.life >= PLATE_MAX_LIFE_S)) gone.push(o);
    }
    if (gone.indexOf(o) < 0) {
      o.mesh.lookAt(camera.position);
      if (o.kind === "clay") o.mesh.rotateZ(3.2 * dt);
    }
  }
  for (const o of gone) {
    missTick(o.mesh ? o.mesh.position.x : 0);
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
  applyLockerLook();

  if (!Bay.over) {
    // Lift mint-tell is afterLiftState audio only. Do not paint VO over the cuff.
    if (!sample.lifted && Bay.wasLifted) {
      Bay.vo(Locker.operator.vo.drop);
    }
  }
  Bay.wasLifted = sample.lifted;

  if (gunGroup) gunGroup.visible = !Bay.over;

  if (Bay.frozen && !Bay.over) {
    Bay.freezeT += dt;
    if (Bay.freezeT >= Bay.freezePadS && !sample.lifted) {
      if (!sharedBay()) Bay.round++;
      Bay.resetRound();
      if (foeGroup) foeGroup.visible = true;
    }
    return;
  }

  if (Bay.over) return;

  if (!sample.lifted) {
    let mx = 0, mz = 0;
    const fwd = Bay.seat === "B" ? 1 : -1;
    if (Bay.keys.w) mz += fwd;
    if (Bay.keys.s) mz -= fwd;
    if (Bay.keys.a) mx += fwd;
    if (Bay.keys.d) mx -= fwd;
    if (mx !== 0 && mz !== 0) { mx *= 0.7071; mz *= 0.7071; }
    const nx = clamp(Bay.pos.x + mx * Bay.speed * dt, -7.6, 7.6);
    const nz = clamp(Bay.pos.z + mz * Bay.speed * dt, -12.2, 13.6);
    if (!bayStallHit(nx, Bay.pos.z)) Bay.pos.x = nx;
    if (!bayStallHit(Bay.pos.x, nz)) Bay.pos.z = nz;
  }
  if (camera) {
    camera.position.set(Bay.pos.x, Bay.pos.y, Bay.pos.z);
    camera.lookAt(Bay.pos.x, 0.89, bayLookZ());
  }

  if (Bay.foe.alive) {
    if (!sharedBay() || !S.bayFoe) {
      Bay.foe.strafeT += dt;
      Bay.foe.x = Math.sin(Bay.foe.strafeT * 0.85) * 2.2;
    }
    if (foeGroup) {
      foeGroup.position.set(Bay.foe.x, 0, Bay.foe.z);
      foeGroup.lookAt(camera.position.x, foeGroup.position.y, camera.position.z);
    }
  }

  if (bayInOpenMiddle(Bay.pos.x, Bay.pos.z)) {
    Bay.expose += dt;
    if (Bay.expose >= Bay.exposeMax) {
      Bay.them++;
      Bay.expose = 0;
      missTick();
      Bay.frozen = true;
      Bay.freezeT = 0;
      if (Bay.them >= Bay.toWin) {
        Bay.over = true;
        Bay.vo(Locker.operator.vo.win);
      }
      if (sharedBay()) {
        try { reportSharedBayFire(aimBus.peek(), true); } catch (e) { /* room is authority */ }
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
  SIT_BOB_RATE,
  SIT_BOB_AMP,
  GRAVITY,
  sitPoseY,
  flyerPose,
  plateRadius,
  rayFromUv,
  raySphere,
  hitscanRange,
  PLATE_MAX_LIFE_S,
  HUD_PAD,
  BAY_TO_WIN,
  BAY_SPEED,
  BAY_EXPOSE_S,
  BAY_FREEZE_PAD_S,
  BAY_FOE_RADIUS,
  BAY_SPAWN_A,
  BAY_SPAWN_B,
  Bay,
  bayInLeftWindow,
  bayInRightAngle,
  bayInOpenMiddle,
  bayStallHit,
  bayCoverChip,
  applyLockerLook,
  rayHitsBayFoe,
  speak,
  unlockAudio,
  bang,
  hitBlip,
  missTick,
  pullWhistle,
  liftMint,
  mintTell,
  afterLiftState,
  YARD_PEEKS,
  init3D,
  fireBay3D,
  createTargetMesh,
  spawnOrb3D,
  worldToHud,
  shatterTarget3D,
  addBulletTracer,
  sharedMatch,
  sharedBay,
  reportSharedFire,
  reportSharedBayFire,
  reportSharedBayPose,
  applySharedBay,
  pullSharedBay,
  spawnSharedPlate,
  applySharedSim,
  pullSharedSim,
  restoreYardLook,
  startBay,
  startWaitingYard,
  startRange,
  randomOrb,
  popup,
  desiredOrbCount,
  galleryOver,
  galleryLeftMs,
  gallerySessionLabel,
  bayOver,
  baySessionLabel,
  updateRange,
  tickBay,
};
