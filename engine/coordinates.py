"""Coordinate transformations and launch-plane utilities."""

import numpy as np
from .constants import RE, E2, FLAT, Z_AXIS, D2R, R2D


def gmst(jd: float) -> float:
    """Greenwich Mean Sidereal Time (rad) from Julian Date."""
    d = jd - 2451545.0
    T = d / 36525.0
    g = 280.46061837 + 360.98564736629 * d + 0.000387933 * T * T - T * T * T / 38710000.0
    return (g % 360.0) * D2R


def geodetic_to_ecef(lat_deg: float, lon_deg: float, h: float) -> np.ndarray:
    """Convert geodetic (deg, deg, m) to ECEF (m)."""
    lat = lat_deg * D2R
    lon = lon_deg * D2R
    N = RE / np.sqrt(1.0 - E2 * np.sin(lat) ** 2)
    return np.array([
        (N + h) * np.cos(lat) * np.cos(lon),
        (N + h) * np.cos(lat) * np.sin(lon),
        (N * (1.0 - E2) + h) * np.sin(lat),
    ])


def ecef_to_geodetic(r: np.ndarray):
    """Convert ECEF (m) to geodetic latitude (deg), longitude (deg), height (m)."""
    x, y, z = r
    lon = np.arctan2(y, x)
    p = np.hypot(x, y)
    if p < 1e-9:
        return (90.0 if z > 0 else -90.0), lon * R2D, abs(z) - RE * (1.0 - FLAT)
    b = RE * (1.0 - FLAT)
    ep2 = (RE ** 2 - b ** 2) / b ** 2
    th = np.arctan2(z * RE, p * b)
    lat = np.arctan2(
        z + ep2 * b * np.sin(th) ** 3,
        p - E2 * RE * np.cos(th) ** 3,
    )
    N = RE / np.sqrt(1.0 - E2 * np.sin(lat) ** 2)
    alt = p / np.cos(lat) - N
    return lat * R2D, lon * R2D, alt


def eci_to_geodetic(r_eci: np.ndarray, theta: float):
    """Convert ECI position to geodetic using GMST angle theta (rad)."""
    c, s = np.cos(-theta), np.sin(-theta)
    r_ecef = np.array([
        c * r_eci[0] - s * r_eci[1],
        s * r_eci[0] + c * r_eci[1],
        r_eci[2],
    ])
    return ecef_to_geodetic(r_ecef)


def enu_basis(r_eci: np.ndarray):
    """Return local East, North, Up unit vectors in the ECI frame."""
    up = r_eci / np.linalg.norm(r_eci)
    e = np.cross(Z_AXIS, up)
    n_e = np.linalg.norm(e)
    e = np.array([1.0, 0.0, 0.0]) if n_e < 1e-9 else e / n_e
    n = np.cross(up, e)
    return e, n, up


def launch_plane_normal(r_eci: np.ndarray, azimuth_deg: float) -> np.ndarray:
    """Inertial normal of the plane defined by the launch-site compass azimuth."""
    e, n, up = enu_basis(r_eci)
    az = float(azimuth_deg) * D2R
    horizontal = np.sin(az) * e + np.cos(az) * n
    normal = np.cross(up, horizontal)
    return normal / max(np.linalg.norm(normal), 1e-12)
