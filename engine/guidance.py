"""Ascent steering laws: vertical, pitch-kick, gravity-turn, simple capture."""

import numpy as np
from .constants import MU, D2R
from .coordinates import enu_basis


def gravity_turn_direction(r: np.ndarray, v: np.ndarray, plane_normal: np.ndarray,
                           launch_horizontal: np.ndarray) -> np.ndarray:
    """Unit thrust direction following velocity projected into the launch plane."""
    up = r / np.linalg.norm(r)
    v_plane = v - np.dot(v, plane_normal) * plane_normal
    nv = np.linalg.norm(v_plane)
    if nv < 1.0:
        # Still nearly vertical – blend toward launch horizontal
        return 0.98 * up + 0.02 * launch_horizontal
    return v_plane / nv


def pitch_kick_direction(r: np.ndarray, plane_normal: np.ndarray,
                         launch_horizontal: np.ndarray,
                         kick_angle_deg: float, fraction: float) -> np.ndarray:
    """Linear pitch program from vertical to kick_angle."""
    up = r / np.linalg.norm(r)
    horiz = np.cross(plane_normal, up)
    nh = np.linalg.norm(horiz)
    horiz = horiz / nh if nh > 1e-9 else launch_horizontal
    p = kick_angle_deg * D2R * np.clip(fraction, 0.0, 1.0)
    return np.cos(p) * up + np.sin(p) * horiz


def simple_capture_direction(r: np.ndarray, v: np.ndarray, target_radius: float,
                             plane_normal: np.ndarray, thrust_accel: float,
                             max_radial_frac: float = 0.45) -> np.ndarray:
    """Simple closed-loop radial-velocity control toward target radius."""
    rn = np.linalg.norm(r)
    up = r / rn
    v_plane = v - np.dot(v, plane_normal) * plane_normal
    v_rad = float(np.dot(v_plane, up))
    v_tang = v_plane - v_rad * up
    vt = np.linalg.norm(v_tang)
    if vt < 1.0:
        return up
    tangent = v_tang / vt

    # Desired radial rate to reach target in ~tau seconds
    tau = 280.0
    v_rad_des = np.clip((target_radius - rn) / tau, -80.0, 900.0)
    err = v_rad_des - v_rad
    # Approximate environment radial accel
    a_env = vt ** 2 / rn - MU / rn ** 2
    a_des = err / tau - a_env
    radial_frac = np.clip(a_des / max(thrust_accel, 1e-6), -max_radial_frac, max_radial_frac)
    tang_frac = np.sqrt(max(0.0, 1.0 - radial_frac ** 2))
    direction = tang_frac * tangent + radial_frac * up
    return direction / max(np.linalg.norm(direction), 1e-12)
