/** Ascent steering laws */
import { MU, D2R } from './constants.js';

function norm(v) { return Math.hypot(...v); }
function scale(v, s) { return v.map(x => x * s); }
function add(a, b) { return a.map((x, i) => x + b[i]); }
function sub(a, b) { return a.map((x, i) => x - b[i]); }
function dot(a, b) { return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]; }
function cross(a, b) {
  return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
}

export function gravityTurnDirection(r, v, planeNormal, launchHoriz) {
  const up = scale(r, 1 / norm(r));
  const vPlane = sub(v, scale(planeNormal, dot(v, planeNormal)));
  const nv = norm(vPlane);
  if (nv < 1) return add(scale(up, 0.98), scale(launchHoriz, 0.02));
  return scale(vPlane, 1 / nv);
}

export function pitchKickDirection(r, planeNormal, launchHoriz, kickAngleDeg, fraction) {
  const up = scale(r, 1 / norm(r));
  let horiz = cross(planeNormal, up);
  const nh = norm(horiz);
  horiz = nh > 1e-9 ? scale(horiz, 1 / nh) : launchHoriz;
  const p = kickAngleDeg * D2R * Math.max(0, Math.min(1, fraction));
  return add(scale(up, Math.cos(p)), scale(horiz, Math.sin(p)));
}

export function simpleCaptureDirection(r, v, targetRadius, planeNormal, thrustAccel, maxRadialFrac = 0.45) {
  const rn = norm(r);
  const up = scale(r, 1 / rn);
  const vPlane = sub(v, scale(planeNormal, dot(v, planeNormal)));
  const vRad = dot(vPlane, up);
  const vTang = sub(vPlane, scale(up, vRad));
  const vt = norm(vTang);
  if (vt < 1) return up;
  const tangent = scale(vTang, 1 / vt);

  const tau = 280;
  const vRadDes = Math.max(-80, Math.min(900, (targetRadius - rn) / tau));
  const err = vRadDes - vRad;
  const aEnv = (vt ** 2) / rn - MU / (rn ** 2);
  const aDes = err / tau - aEnv;
  let radialFrac = aDes / Math.max(thrustAccel, 1e-6);
  radialFrac = Math.max(-maxRadialFrac, Math.min(maxRadialFrac, radialFrac));
  const tangFrac = Math.sqrt(Math.max(0, 1 - radialFrac ** 2));
  const dir = add(scale(tangent, tangFrac), scale(up, radialFrac));
  return scale(dir, 1 / Math.max(norm(dir), 1e-12));
}
