/** US Standard Atmosphere 1976 + exponential extension */
import { G0, R_AIR, GAMMA } from './constants.js';

const LAYERS = [
  [0, 288.15, -0.0065, 101325],
  [11000, 216.65, 0, 22632.1],
  [20000, 216.65, 0.001, 5474.89],
  [32000, 228.65, 0.0028, 868.019],
  [47000, 270.65, 0, 110.906],
  [51000, 270.65, -0.0028, 66.9389],
  [71000, 214.65, -0.002, 3.95642],
];
const H_TOP = 84852, T_TOP = 186.946, P_TOP = 0.37287, HS = 6500;

const MACH = [0, 0.5, 0.8, 1, 1.2, 1.5, 2, 3, 5, 10, 25];
const CD   = [0.30, 0.30, 0.34, 0.58, 0.62, 0.55, 0.45, 0.33, 0.28, 0.26, 0.25];

export function atmosphere(h) {
  if (h <= 0) h = 0;
  let T, p;
  if (h >= H_TOP) {
    T = T_TOP;
    p = P_TOP * Math.exp(-(h - H_TOP) / HS);
  } else {
    let hb = LAYERS[0][0], Tb = LAYERS[0][1], L = LAYERS[0][2], pb = LAYERS[0][3];
    for (const lay of LAYERS) {
      if (h >= lay[0]) { hb = lay[0]; Tb = lay[1]; L = lay[2]; pb = lay[3]; }
      else break;
    }
    if (Math.abs(L) < 1e-12) {
      T = Tb;
      p = pb * Math.exp(-G0 * (h - hb) / (R_AIR * Tb));
    } else {
      T = Math.max(Tb + L * (h - hb), 1);
      p = pb * Math.pow(T / Tb, -G0 / (L * R_AIR));
    }
  }
  const rho = p / (R_AIR * T);
  const a = Math.sqrt(GAMMA * R_AIR * T);
  return { rho, p, T, a };
}

export function dragCoefficient(mach) {
  if (mach <= MACH[0]) return CD[0];
  if (mach >= MACH[MACH.length - 1]) return CD[CD.length - 1];
  for (let i = 0; i < MACH.length - 1; i++) {
    if (mach >= MACH[i] && mach <= MACH[i + 1]) {
      const f = (mach - MACH[i]) / (MACH[i + 1] - MACH[i]);
      return CD[i] + f * (CD[i + 1] - CD[i]);
    }
  }
  return 0.25;
}
