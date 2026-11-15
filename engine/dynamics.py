"""3-DOF ascent dynamics with J2 gravity and atmosphere."""

import numpy as np
from .constants import MU, RE, J2, OMEGA_E, G0
from .atmosphere import atmosphere, drag_coefficient
from .coordinates import eci_to_geodetic


def two_body_j2_accel(r: np.ndarray) -> np.ndarray:
    """Acceleration due to central gravity + J2 (m/s²)."""
    rn = np.linalg.norm(r)
    zr = r[2] / rn
    k = -MU / rn ** 3
    j = 1.5 * J2 * MU * RE ** 2 / rn ** 5
    return k * r + np.array([
        j * r[0] * (5 * zr ** 2 - 1),
        j * r[1] * (5 * zr ** 2 - 1),
        j * r[2] * (5 * zr ** 2 - 3),
    ])


def deriv(state: np.ndarray, mass: float, thr_vec: np.ndarray, alt: float,
          area: float) -> np.ndarray:
    """State derivative [vx,vy,vz, ax,ay,az]."""
    r, v = state[0:3], state[3:6]
    ag = two_body_j2_accel(r)

    # Drag in rotating atmosphere
    v_rel = v - np.cross(np.array([0.0, 0.0, OMEGA_E]), r)
    vr = np.linalg.norm(v_rel)
    ad = np.zeros(3)
    if vr > 1.0:
        rho, _, _, a_snd = atmosphere(alt)
        if rho > 1e-12:
            cd = drag_coefficient(vr / max(a_snd, 1.0))
            ad = -0.5 * rho * vr * cd * area / max(mass, 1.0) * v_rel

    return np.concatenate([v, ag + thr_vec / max(mass, 1.0) + ad])


def rk4_step(state: np.ndarray, mass: float, thr_vec: np.ndarray, alt: float,
             area: float, dt: float) -> np.ndarray:
    """Single RK4 integration step."""
    k1 = deriv(state, mass, thr_vec, alt, area)
    k2 = deriv(state + 0.5 * dt * k1, mass, thr_vec, alt, area)
    k3 = deriv(state + 0.5 * dt * k2, mass, thr_vec, alt, area)
    k4 = deriv(state + dt * k3, mass, thr_vec, alt, area)
    return state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
