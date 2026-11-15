"""Full multi-stage ascent simulation for ASTROCAM."""

from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd

from .constants import RE, OMEGA_E, MU, G0, D2R
from .coordinates import geodetic_to_ecef, eci_to_geodetic, gmst, enu_basis, launch_plane_normal
from .atmosphere import atmosphere
from .dynamics import rk4_step
from .guidance import gravity_turn_direction, pitch_kick_direction, simple_capture_direction
from .vehicle import Vehicle, Stage
from .visibility import look_angles, is_illuminated


def simulate_ascent(
    vehicle: Vehicle,
    site_lat: float,
    site_lon: float,
    site_alt: float,
    launch_azimuth_deg: float,
    launch_jd: float,
    target_alt: float = 400e3,
    vertical_time: float = 10.0,
    kick_angle: float = 7.0,
    kick_duration: float = 14.0,
    dt: float = 0.1,
    dt_out: float = 1.0,
    max_time: float = 1800.0,
    obs_lat: Optional[float] = None,
    obs_lon: Optional[float] = None,
    obs_alt: float = 0.0,
) -> Tuple[pd.DataFrame, np.ndarray, float]:
    """Simulate powered ascent and return telemetry dataframe + final state."""

    theta0 = gmst(launch_jd)
    az = launch_azimuth_deg * D2R

    # Initial state in ECI
    r_ecef = geodetic_to_ecef(site_lat, site_lon, site_alt)
    c, s = np.cos(theta0), np.sin(theta0)
    r = np.array([c * r_ecef[0] - s * r_ecef[1],
                  s * r_ecef[0] + c * r_ecef[1],
                  r_ecef[2]])
    v = np.cross(np.array([0.0, 0.0, OMEGA_E]), r)
    state = np.concatenate([r, v])

    plane_normal = launch_plane_normal(r, launch_azimuth_deg)
    e0, n0, up0 = enu_basis(r)
    launch_horizontal = np.sin(az) * e0 + np.cos(az) * n0

    stages = vehicle.stages
    prop_left = [sg.prop_mass for sg in stages]
    stage_time = [0.0 for _ in stages]
    idx = 0
    ignite_at = 0.0
    fairing_on = True
    apo_lock = False
    t = 0.0
    target_r = RE + target_alt

    rows = []
    next_out = 0.0

    def current_mass():
        m = vehicle.payload + (vehicle.fairing_mass if fairing_on else 0.0)
        for i in range(idx, len(stages)):
            m += stages[i].dry_mass + prop_left[i]
        return m

    while t < max_time:
        rn = np.linalg.norm(state[0:3])
        lat_d, lon_d, alt = eci_to_geodetic(state[0:3], theta0 + OMEGA_E * t)
        if alt < -500.0:
            break

        # Fairing jettison
        if fairing_on:
            if vehicle.fairing_jettison_t is not None:
                if t >= vehicle.fairing_jettison_t:
                    fairing_on = False
            elif alt >= vehicle.fairing_jettison_alt:
                fairing_on = False

        # Stage separation / ignition logic
        if idx < len(stages) and stages[idx].separation_t is not None and t >= stages[idx].separation_t:
            idx += 1
            if idx >= len(stages):
                break
            ignite_at = t
            continue

        if idx < len(stages) and stages[idx].burn_windows is not None:
            burning = (prop_left[idx] > 0.0 and
                       any(start <= t < end for start, end in stages[idx].burn_windows))
        else:
            burning = (idx < len(stages) and prop_left[idx] > 0.0
                       and stage_time[idx] < stages[idx].burn_time
                       and t >= ignite_at)

        # Advance stage index when burn finishes (legacy continuous burn)
        if (idx < len(stages) and stages[idx].burn_windows is None
                and not burning and t >= ignite_at
                and (prop_left[idx] <= 0.0 or stage_time[idx] >= stages[idx].burn_time - 1e-9)):
            if idx + 1 < len(stages):
                idx += 1
                ignite_at = t + max(stages[idx].ignition_delay, 0.0)
                continue
            else:
                break

        # Capture lock
        if not apo_lock and alt > 60000.0:
            # Simple predicted apoapsis check
            energy = 0.5 * np.dot(state[3:6], state[3:6]) - MU / rn
            if energy < 0:
                a = -MU / (2 * energy)
                h = np.cross(state[0:3], state[3:6])
                e_vec = np.cross(state[3:6], h) / MU - state[0:3] / rn
                ra = a * (1 + np.linalg.norm(e_vec))
                if ra > RE + 120e3:
                    apo_lock = True

        mass = current_mass()
        if burning:
            stg = stages[idx]
            rho, p, _, _ = atmosphere(alt)
            thr = stg.thrust(p, stage_time[idx])
            isp = stg.isp(p)
            mdot = thr / (G0 * isp) if isp > 1.0 else 0.0
        else:
            thr, mdot = 0.0, 0.0

        thrust_accel = thr / max(mass, 1.0)

        # Steering
        if not burning:
            u = state[3:6] / max(np.linalg.norm(state[3:6]), 1e-9)
        elif t < vertical_time:
            u = state[0:3] / rn
        elif t < vertical_time + kick_duration:
            frac = (t - vertical_time) / max(kick_duration, 1e-6)
            u = pitch_kick_direction(state[0:3], plane_normal, launch_horizontal,
                                     kick_angle, frac)
        elif apo_lock:
            u = simple_capture_direction(state[0:3], state[3:6], target_r,
                                         plane_normal, thrust_accel)
        else:
            u = gravity_turn_direction(state[0:3], state[3:6], plane_normal,
                                       launch_horizontal)

        u = u / max(np.linalg.norm(u), 1e-9)
        thr_vec = thr * u
        area = stages[idx].area if idx < len(stages) else stages[-1].area

        # Output sample
        if t >= next_out - 1e-9:
            v_rel = state[3:6] - np.cross(np.array([0.0, 0.0, OMEGA_E]), state[0:3])
            speed = float(np.linalg.norm(v_rel))
            up = state[0:3] / rn
            v_rad = float(np.dot(v_rel, up))
            v_tang = float(np.sqrt(max(speed**2 - v_rad**2, 0.0)))

            az_obs = el_obs = el_app = rng = None
            illuminated = None
            if obs_lat is not None and obs_lon is not None:
                az_obs, el_obs, rng, el_app = look_angles(
                    state[0:3], obs_lat, obs_lon, obs_alt,
                    launch_jd + t / 86400.0, theta0 + OMEGA_E * t
                )
                illuminated = is_illuminated(state[0:3], launch_jd + t / 86400.0)

            rows.append({
                "t": round(t, 2),
                "alt_km": round(alt / 1000.0, 3),
                "lat": round(lat_d, 5),
                "lon": round(lon_d, 5),
                "v_mps": round(speed, 1),
                "v_radial": round(v_rad, 1),
                "v_tangential": round(v_tang, 1),
                "mass_kg": round(mass, 1),
                "thrust_kN": round(thr / 1000.0, 2),
                "stage": stages[idx].name if idx < len(stages) else "coast",
                "az_deg": None if az_obs is None else round(az_obs, 2),
                "el_deg": None if el_obs is None else round(el_obs, 2),
                "el_apparent_deg": None if el_app is None else round(el_app, 2),
                "range_km": None if rng is None else round(rng / 1000.0, 1),
                "illuminated": illuminated,
            })
            next_out += dt_out

        # Integrate
        state = rk4_step(state, mass, thr_vec, alt, area, dt)
        if burning and mdot > 0:
            dp = mdot * dt
            prop_left[idx] = max(0.0, prop_left[idx] - dp)
            stage_time[idx] += dt
        t += dt

    df = pd.DataFrame(rows)
    return df, state, t
