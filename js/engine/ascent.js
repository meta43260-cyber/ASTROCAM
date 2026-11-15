/** Full multi-stage ascent simulation (client-side) */
import { RE, OMEGA_E, MU, G0, D2R } from './constants.js';
import { geodeticToEcef, eciToGeodetic, gmst, enuBasis, launchPlaneNormal } from './coordinates.js';
import { atmosphere } from './atmosphere.js';
import { rk4Step } from './dynamics.js';
import { gravityTurnDirection, pitchKickDirection, simpleCaptureDirection } from './guidance.js';
import { lookAngles, isIlluminated } from './visibility.js';

function norm(v) { return Math.hypot(...v); }
function scale(v, s) { return v.map(x => x * s); }
function cross(a, b) {
  return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
}

export function simulateAscent({
  vehicle,
  siteLat, siteLon, siteAlt = 0,
  launchAzimuthDeg,
  launchJd,
  targetAlt = 400e3,
  verticalTime = 10,
  kickAngle = 7,
  kickDuration = 14,
  dt = 0.15,
  dtOut = 1.5,
  maxTime = 1600,
  obsLat = null, obsLon = null, obsAlt = 0,
}) {
  const theta0 = gmst(launchJd);
  const az = launchAzimuthDeg * D2R;

  const rEcef = geodeticToEcef(siteLat, siteLon, siteAlt);
  const c = Math.cos(theta0), s = Math.sin(theta0);
  let r = [c*rEcef[0]-s*rEcef[1], s*rEcef[0]+c*rEcef[1], rEcef[2]];
  let v = cross([0, 0, OMEGA_E], r);
  let state = [...r, ...v];

  const planeNormal = launchPlaneNormal(r, launchAzimuthDeg);
  const { e, n, up: up0 } = enuBasis(r);
  const launchHoriz = [
    Math.sin(az)*e[0] + Math.cos(az)*n[0],
    Math.sin(az)*e[1] + Math.cos(az)*n[1],
    Math.sin(az)*e[2] + Math.cos(az)*n[2],
  ];

  const stages = vehicle.stages;
  const propLeft = stages.map(s => s.propMass);
  const stageTime = stages.map(() => 0);
  let idx = 0;
  let igniteAt = 0;
  let fairingOn = true;
  let apoLock = false;
  let t = 0;
  const targetR = RE + targetAlt;
  const rows = [];
  let nextOut = 0;

  function currentMass() {
    let m = vehicle.payload + (fairingOn ? vehicle.fairingMass : 0);
    for (let i = idx; i < stages.length; i++) m += stages[i].dryMass + propLeft[i];
    return m;
  }

  while (t < maxTime) {
    const rn = norm(state.slice(0, 3));
    const [lat, lon, alt] = eciToGeodetic(state.slice(0, 3), theta0 + OMEGA_E * t);
    if (alt < -500) break;

    if (fairingOn && alt >= vehicle.fairingJettisonAlt) fairingOn = false;

    let burning = false;
    if (idx < stages.length) {
      burning = propLeft[idx] > 0 && stageTime[idx] < stages[idx].burnTime && t >= igniteAt;
    }

    if (idx < stages.length && !burning && t >= igniteAt &&
        (propLeft[idx] <= 0 || stageTime[idx] >= stages[idx].burnTime - 1e-9)) {
      if (idx + 1 < stages.length) {
        idx++;
        igniteAt = t + (stages[idx].ignitionDelay || 0);
        continue;
      } else break;
    }

    if (!apoLock && alt > 60000) {
      const vv = state.slice(3, 6);
      const speed2 = vv[0]**2 + vv[1]**2 + vv[2]**2;
      const energy = 0.5 * speed2 - MU / rn;
      if (energy < 0) {
        const a = -MU / (2 * energy);
        const h = cross(state.slice(0, 3), vv);
        const eVec = [
          (vv[1]*h[2]-vv[2]*h[1])/MU - state[0]/rn,
          (vv[2]*h[0]-vv[0]*h[2])/MU - state[1]/rn,
          (vv[0]*h[1]-vv[1]*h[0])/MU - state[2]/rn,
        ];
        const ra = a * (1 + norm(eVec));
        if (ra > RE + 120e3) apoLock = true;
      }
    }

    const mass = currentMass();
    let thr = 0, mdot = 0;
    if (burning) {
      const { p } = atmosphere(alt);
      thr = stages[idx].thrust(p, stageTime[idx]);
      const isp = stages[idx].isp(p);
      mdot = isp > 1 ? thr / (G0 * isp) : 0;
    }
    const thrustAccel = thr / Math.max(mass, 1);

    let u;
    if (!burning) {
      const vv = state.slice(3, 6);
      const nv = norm(vv);
      u = nv > 1e-6 ? scale(vv, 1/nv) : scale(state.slice(0,3), 1/rn);
    } else if (t < verticalTime) {
      u = scale(state.slice(0, 3), 1 / rn);
    } else if (t < verticalTime + kickDuration) {
      const frac = (t - verticalTime) / Math.max(kickDuration, 1e-6);
      u = pitchKickDirection(state.slice(0,3), planeNormal, launchHoriz, kickAngle, frac);
    } else if (apoLock) {
      u = simpleCaptureDirection(state.slice(0,3), state.slice(3,6), targetR, planeNormal, thrustAccel);
    } else {
      u = gravityTurnDirection(state.slice(0,3), state.slice(3,6), planeNormal, launchHoriz);
    }
    const nu = norm(u);
    u = scale(u, 1 / Math.max(nu, 1e-9));
    const thrVec = scale(u, thr);
    const area = idx < stages.length ? stages[idx].area : stages[stages.length-1].area;

    if (t >= nextOut - 1e-9) {
      const vRel = [
        state[3] - (-OMEGA_E * state[1]),
        state[4] - ( OMEGA_E * state[0]),
        state[5],
      ];
      const speed = norm(vRel);
      const up = scale(state.slice(0,3), 1/rn);
      const vRad = up[0]*vRel[0] + up[1]*vRel[1] + up[2]*vRel[2];
      const vTang = Math.sqrt(Math.max(0, speed*speed - vRad*vRad));

      let azObs = null, elObs = null, elApp = null, rng = null, illum = null;
      if (obsLat != null && obsLon != null) {
        const la = lookAngles(state.slice(0,3), obsLat, obsLon, obsAlt,
                              launchJd + t/86400, theta0 + OMEGA_E*t);
        azObs = la.az; elObs = la.el; elApp = la.elApp; rng = la.range;
        illum = isIlluminated(state.slice(0,3), launchJd + t/86400);
      }

      rows.push({
        t: +t.toFixed(2),
        alt_km: +(alt/1000).toFixed(3),
        lat: +lat.toFixed(5),
        lon: +lon.toFixed(5),
        v_mps: +speed.toFixed(1),
        v_radial: +vRad.toFixed(1),
        v_tangential: +vTang.toFixed(1),
        mass_kg: +mass.toFixed(0),
        thrust_kN: +(thr/1000).toFixed(2),
        stage: idx < stages.length ? stages[idx].name : 'coast',
        az_deg: azObs != null ? +azObs.toFixed(2) : null,
        el_deg: elObs != null ? +elObs.toFixed(2) : null,
        el_apparent_deg: elApp != null ? +elApp.toFixed(2) : null,
        range_km: rng != null ? +(rng/1000).toFixed(1) : null,
        illuminated: illum,
      });
      nextOut += dtOut;
    }

    state = rk4Step(state, mass, thrVec, alt, area, dt);
    if (burning && mdot > 0) {
      propLeft[idx] = Math.max(0, propLeft[idx] - mdot * dt);
      stageTime[idx] += dt;
    }
    t += dt;
  }

  return { samples: rows, tEnd: t, finalState: state };
}
