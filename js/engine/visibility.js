/** Look angles, refraction, illumination */
import { RE, R2D } from './constants.js';
import { geodeticToEcef, enuBasis } from './coordinates.js';

export function sunUnitEci(jd) {
  const n = jd - 2451545;
  const L = ((280.460 + 0.9856474 * n) % 360) * Math.PI / 180;
  const g = ((357.528 + 0.9856003 * n) % 360) * Math.PI / 180;
  const lam = L + (1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * Math.PI / 180;
  const eps = (23.439 - 4e-7 * n) * Math.PI / 180;
  return [Math.cos(lam), Math.cos(eps) * Math.sin(lam), Math.sin(eps) * Math.sin(lam)];
}

export function applyRefraction(elDeg, pressureHpa = 1013.25, tempC = 15) {
  if (elDeg < -1) return elDeg;
  let R = 1.02 / Math.tan((elDeg + 10.3 / (elDeg + 5.11)) * Math.PI / 180);
  R *= (pressureHpa / 1010) * (283 / (273 + tempC));
  return elDeg + R / 60;
}

export function lookAngles(rSatEci, obsLat, obsLon, obsAlt, jd, theta0, useRefraction = true) {
  const rObsEcef = geodeticToEcef(obsLat, obsLon, obsAlt);
  const c = Math.cos(theta0), s = Math.sin(theta0);
  const rObs = [c * rObsEcef[0] - s * rObsEcef[1], s * rObsEcef[0] + c * rObsEcef[1], rObsEcef[2]];

  const rho = [rSatEci[0]-rObs[0], rSatEci[1]-rObs[1], rSatEci[2]-rObs[2]];
  const range = Math.hypot(...rho);
  if (range < 1) return { az: 0, el: 90, range, elApp: 90 };

  const { e, n, up } = enuBasis(rObs);
  const east = rho[0]*e[0] + rho[1]*e[1] + rho[2]*e[2];
  const north = rho[0]*n[0] + rho[1]*n[1] + rho[2]*n[2];
  const upComp = rho[0]*up[0] + rho[1]*up[1] + rho[2]*up[2];

  let az = Math.atan2(east, north) * R2D;
  if (az < 0) az += 360;
  const el = Math.asin(Math.max(-1, Math.min(1, upComp / range))) * R2D;
  const elApp = useRefraction ? applyRefraction(el) : el;
  return { az, el, range, elApp };
}

export function isIlluminated(rSatEci, jd, marginKm = 0) {
  const sun = sunUnitEci(jd);
  const rn = Math.hypot(...rSatEci);
  const cosAngle = -(rSatEci[0]*sun[0] + rSatEci[1]*sun[1] + rSatEci[2]*sun[2]) / rn;
  const sinEarth = (RE + marginKm * 1000) / rn;
  if (sinEarth >= 1) return false;
  return cosAngle < Math.sqrt(Math.max(0, 1 - sinEarth ** 2));
}
