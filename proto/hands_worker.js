/* SABLE — hands_worker.js
   Classic worker (not type:module). MediaPipe wasm glue calls importScripts.
   GPU first, CPU fallback. Main applies One Euro. Fire never waits here. */

const BASE = {
  runningMode: "VIDEO",
  numHands: 2,
  minHandDetectionConfidence: 0.45,
  minHandPresenceConfidence: 0.45,
  minTrackingConfidence: 0.45,
};

let landmarker = null;
let delegate = "";

function packLandmarks(res) {
  const lms = res && res.landmarks;
  if (!lms || !lms.length) return [];
  const out = [];
  for (let i = 0; i < lms.length; i++) {
    const hand = lms[i];
    if (!hand) continue;
    const pts = [];
    for (let j = 0; j < hand.length; j++) {
      const p = hand[j];
      pts.push({ x: p.x, y: p.y, z: p.z || 0 });
    }
    out.push(pts);
  }
  return out;
}

async function createLandmarker(mod, vision, model, want) {
  return mod.HandLandmarker.createFromOptions(vision, Object.assign({
    baseOptions: { modelAssetPath: model, delegate: want },
  }, BASE));
}

async function init(tries) {
  let last = null;
  for (let i = 0; i < tries.length; i++) {
    const t = tries[i];
    try {
      const mod = await import(t.js);
      const vision = await mod.FilesetResolver.forVisionTasks(t.wasm);
      try {
        landmarker = await createLandmarker(mod, vision, t.model, "GPU");
        delegate = "GPU";
      } catch (e) {
        landmarker = await createLandmarker(mod, vision, t.model, "CPU");
        delegate = "CPU";
      }
      self.postMessage({ type: "ready", delegate });
      return;
    } catch (e) {
      last = e;
    }
  }
  throw last || new Error("HandLandmarker worker init failed");
}

self.onmessage = async (ev) => {
  const msg = ev.data || {};
  if (msg.type === "init") {
    try {
      await init(msg.tries || []);
    } catch (e) {
      self.postMessage({ type: "fail", error: String(e && e.message ? e.message : e) });
    }
    return;
  }
  if (msg.type === "frame") {
    const bmp = msg.bitmap;
    const ts = msg.ts;
    let landmarks = [];
    try {
      if (landmarker && bmp) {
        landmarks = packLandmarks(landmarker.detectForVideo(bmp, ts));
      }
    } catch (e) {
      landmarks = [];
    }
    if (bmp && typeof bmp.close === "function") {
      try { bmp.close(); } catch (e) { /* already transferred/closed */ }
    }
    self.postMessage({ type: "result", ts, landmarks, delegate });
  }
};
