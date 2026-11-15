/** Coordinate transforms and launch-plane utilities */
import { RE, E2, FLAT, Z_AXIS, D2R, R2D } from './constants.js';

export function gmst(jd) {
  const d = jd - 2451545;
  const T = d / 36525;
  let g = 280.46061837 + 360.98564736629 * d + 0.000387933 * T * T - T * T * T / 38710000;
  return ((g % 360) + 360) % 360 * D2R;
}

export function geodeticToEcef(latDeg, lonDeg, h) {
  const lat = latDeg * D2R, lon = lonDeg * D2R;
  const N = RE / Math.sqrt(1 - E2 * Math.sin(lat) ** 2);
  return [
    (N + h) * Math.cos(lat) * Math.cos(lon),
    (N + h) * Math.cos(lat) * Math.sin(lon),
    (N * (1 - E2) + h) * Math.sin(lat),
  ];
}

export function ecefToGeodetic(r) {
  const [x, y, z] = r;
  const lon = Math.atan2(y, x);
  const p = Math.hypot(x, y);
  if (p < 1e-9) return [z > 0 ? 90 : -90, lon * R2D, Math.abs(z) - RE * (1 - FLAT)];
  const b = RE * (1 - FLAT);
  const ep2 = (RE ** 2 - b ** 2) / b ** 2;
  const th = Math.atan2(z * RE, p * b);
  const lat = Math.atan2(z + ep2 * b * Math.sin(th) ** 3, p - E2 * RE * Math.cos(th) ** 3);
  const N = RE / Math.sqrt(1 - E2 * Math.sin(lat) ** 2);
  const alt = p / Math.cos(lat) - N;
  return [lat * R2D, lon * R2D, alt];
}

export function eciToGeodetic(rEci, theta) {
  const c = Math.cos(-theta), s = Math.sin(-theta);
  const rEcef = [c * rEci[0] - s * rEci[1], s * rEci[0] + c * rEci[1], rEci[2]];
  return ecefToGeodetic(rEcef);
}

export function enuBasis(rEci) {
  const rn = Math.hypot(...rEci);
  const up = rEci.map(v => v / rn);
  let e = cross(Z_AXIS, up);
  const ne = Math.hypot(...e);
  e = ne < 1e-9 ? [1, 0, 0] : e.map(v => v / ne);
  const n = cross(up, e);
  return { e, n, up };
}

export function launchPlaneNormal(rEci, azimuthDeg) {
  const { e, n, up } = enuBasis(rEci);
  const az = azimuthDeg * D2R;
  const horiz = [Math.sin(az) * e[0] + Math.cos(az) * n[0],
                 Math.sin(az) * e[1] + Math.cos(az) * n[1],
                 Math.sin(az) * e[2] + Math.cos(az) * n[2]];
  const normal = cross(up, horiz);
  const nn = Math.hypot(...normal);
  return normal.map(v => v / Math.max(nn, 1e-12));
}

function cross(a, b) {
  return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
}
