/* SABLE — port.js
   SablePort ownership. Host-adapter seams for a later migrate.
   Current host is SABLE original IP. Runtime identity never names a
   third-party title, map, or gun. Feeling / architecture: docs/port.md.
   This module must not change fire, tick, Look, HUD, or audio. */

export const SABLE_PORT_HOST = "sable";
export const SABLE_PORT_VERB = "aimbus-hid-peek";
export const SABLE_PORT_SIM_HZ = 128;
export const SABLE_PORT_LOOK = "charcoal-bone-mint-rust";
export const SABLE_PORT_MODES = Object.freeze([
  "gallery",
  "bay",
  "warmup",
  "shared-house",
]);

export function sableHostId() {
  return SABLE_PORT_HOST;
}

export function sableHostFeel() {
  return {
    host: SABLE_PORT_HOST,
    verb: SABLE_PORT_VERB,
    simHz: SABLE_PORT_SIM_HZ,
    look: SABLE_PORT_LOOK,
    modes: SABLE_PORT_MODES,
  };
}

export const SablePort = {
  host: SABLE_PORT_HOST,
  verb: SABLE_PORT_VERB,
  simHz: SABLE_PORT_SIM_HZ,
  look: SABLE_PORT_LOOK,
  modes: SABLE_PORT_MODES,
  id: sableHostId,
  feel: sableHostFeel,
};

if (typeof window !== "undefined") {
  window.SablePort = SablePort;
}
