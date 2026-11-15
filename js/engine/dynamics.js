/** 3DOF dynamics with J2 + drag */
import { MU, RE, J2, OMEGA_E } from './constants.js';
import { atmosphere, dragCoefficient } from './atmosphere.js';

export function twoBodyJ2Accel(r) {
  const rn = Math.hypot(...r);
  const zr = r[2] / rn;
  const k = -MU / (rn ** 3);
  const j = 1.5 * J2 * MU * RE ** 2 / (rn ** 5);
  return [
    k * r[0] + j * r[0] * (5 * zr ** 2 - 1),
    k * r[1] + j * r[1] * (5 * zr ** 2 - 1),
    k * r[2] + j * r[2] * (5 * zr ** 2 - 3),
  ];
}

function deriv(state, mass, thrVec, alt, area) {
  const r = state.slice(0, 3);
  const v = state.slice(3, 6);
  const ag = twoBodyJ2Accel(r);

  const omega = [0, 0, OMEGA_E];
  const vRel = [
    v[0] - (omega[1]*r[2] - omega[2]*r[1]),
    v[1] - (omega[2]*r[0] - omega[0]*r[2]),
    v[2] - (omega[0]*r[1] - omega[1]*r[0]),
  ];
  const vr = Math.hypot(...vRel);
  let ad = [0, 0, 0];
  if (vr > 1) {
    const { rho, a } = atmosphere(alt);
    if (rho > 1e-12) {
      const cd = dragCoefficient(vr / Math.max(a, 1));
      const factor = -0.5 * rho * vr * cd * area / Math.max(mass, 1);
      ad = vRel.map(x => factor * x);
    }
  }
  return [
    v[0], v[1], v[2],
    ag[0] + thrVec[0] / Math.max(mass, 1) + ad[0],
    ag[1] + thrVec[1] / Math.max(mass, 1) + ad[1],
    ag[2] + thrVec[2] / Math.max(mass, 1) + ad[2],
  ];
}

export function rk4Step(state, mass, thrVec, alt, area, dt) {
  const k1 = deriv(state, mass, thrVec, alt, area);
  const s2 = state.map((x, i) => x + 0.5 * dt * k1[i]);
  const k2 = deriv(s2, mass, thrVec, alt, area);
  const s3 = state.map((x, i) => x + 0.5 * dt * k2[i]);
  const k3 = deriv(s3, mass, thrVec, alt, area);
  const s4 = state.map((x, i) => x + dt * k3[i]);
  const k4 = deriv(s4, mass, thrVec, alt, area);
  return state.map((x, i) => x + (dt / 6) * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i]));
}
