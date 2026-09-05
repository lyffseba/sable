/* SABLE — audio.js
   SableAudio: sparse Salt House / gallery verbs.
   Dry-tick miss + hit punch after shot resolve. Quiet mint-tell lift chirp
   after the cuff goes GUN. Original oscillators only. Locked VO copy is
   SABLE_AUDIO_MINT_TELL ("Mint. Lift.") — no browser TTS, no third-party
   voices. Spoken CANCHO later only via original synthesis.
   No bed, no ambience, no third-party packs, no Marketplace SFX. */

export const SABLE_AUDIO_MISS_HZ = 1850;
export const SABLE_AUDIO_MISS_MS = 28;
export const SABLE_AUDIO_HIT_MS = 55;
export const SABLE_AUDIO_GAIN_CAP = 0.12;
export const SABLE_AUDIO_MISS_GAIN = 0.055;
export const SABLE_AUDIO_HIT_GAIN = 0.10;
export const SABLE_AUDIO_HIT_BODY_GAIN = 0.07;
export const SABLE_AUDIO_LIFT_HZ = 1040;
export const SABLE_AUDIO_LIFT_HZ_B = 1480;
export const SABLE_AUDIO_LIFT_MS = 22;
export const SABLE_AUDIO_LIFT_GAIN = 0.028;
export const SABLE_AUDIO_MINT_TELL = "Mint. Lift.";
export const SABLE_AUDIO_PAN_MAX = 0.35;

let actx = null;

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

export function hallPan(x) {
  return clamp((Number(x) || 0) / 12, -SABLE_AUDIO_PAN_MAX, SABLE_AUDIO_PAN_MAX);
}

export function unlockAudio() {
  const AC = typeof window !== "undefined" && (window.AudioContext || window.webkitAudioContext);
  if (!AC) return;
  if (!actx) actx = new AC();
  if (actx.state === "suspended") actx.resume();
}

export function bang() {
  // SablePerf timing hook only. Gallery verbs are missTick / hitBlip after resolve.
}

function tap(freq, durS, gainAmt, type, pan, delayS) {
  if (!actx) return;
  const t = actx.currentTime + (Number(delayS) || 0);
  const osc = actx.createOscillator();
  const gain = actx.createGain();
  const g = Math.min(gainAmt, SABLE_AUDIO_GAIN_CAP);
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t);
  gain.gain.setValueAtTime(g, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + durS);
  osc.connect(gain);
  if (typeof actx.createStereoPanner === "function") {
    const panner = actx.createStereoPanner();
    panner.pan.setValueAtTime(clamp(pan || 0, -SABLE_AUDIO_PAN_MAX, SABLE_AUDIO_PAN_MAX), t);
    gain.connect(panner);
    panner.connect(actx.destination);
  } else {
    gain.connect(actx.destination);
  }
  osc.start(t);
  osc.stop(t + durS + 0.004);
}

export function missTick(worldX) {
  tap(
    SABLE_AUDIO_MISS_HZ,
    SABLE_AUDIO_MISS_MS / 1000,
    SABLE_AUDIO_MISS_GAIN,
    "triangle",
    hallPan(worldX)
  );
}

export function hitBlip(combo, worldX) {
  void combo;
  const pan = hallPan(worldX);
  const dur = SABLE_AUDIO_HIT_MS / 1000;
  tap(210, dur, SABLE_AUDIO_HIT_BODY_GAIN, "sine", pan);
  tap(720, dur * 0.55, SABLE_AUDIO_HIT_GAIN, "triangle", pan);
}

export function pullWhistle() {
  // Gallery cut: no spawn whistle. Miss + hit + lift mint only.
}

export function liftMint(worldX) {
  const pan = hallPan(worldX);
  const dur = SABLE_AUDIO_LIFT_MS / 1000;
  tap(SABLE_AUDIO_LIFT_HZ, dur, SABLE_AUDIO_LIFT_GAIN, "sine", pan, 0);
  tap(SABLE_AUDIO_LIFT_HZ_B, dur, SABLE_AUDIO_LIFT_GAIN, "sine", pan, 0.028);
}

export function mintTell(worldX) {
  // Locked SableCancho line is SABLE_AUDIO_MINT_TELL. This cut ships the
  // oscillator mint chirp — never browser TTS / third-party voices.
  void SABLE_AUDIO_MINT_TELL;
  liftMint(worldX);
}

export const SableAudio = {
  unlock: unlockAudio,
  bang,
  missTick,
  hitBlip,
  pullWhistle,
  liftMint,
  mintTell,
  hallPan,
  MISS_HZ: SABLE_AUDIO_MISS_HZ,
  MISS_MS: SABLE_AUDIO_MISS_MS,
  HIT_MS: SABLE_AUDIO_HIT_MS,
  LIFT_HZ: SABLE_AUDIO_LIFT_HZ,
  LIFT_MS: SABLE_AUDIO_LIFT_MS,
  LIFT_GAIN: SABLE_AUDIO_LIFT_GAIN,
  MINT_TELL: SABLE_AUDIO_MINT_TELL,
  GAIN_CAP: SABLE_AUDIO_GAIN_CAP,
};
