/* SABLE — game.js
   Proto entry. Ownership lives in aim.js, hands.js, house.js, boot.js,
   audio.js, port.js (SablePort host seams — identity only).
   Trackpad / HID click fires from the AimBus mailbox — never waits on camera. */

import "./port.js";
import "./boot.js";
