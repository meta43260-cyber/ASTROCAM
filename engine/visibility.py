"""Observer look angles, atmospheric refraction, and illumination."""

import numpy as np
from .constants import RE, R2D
from .coordinates import geodetic_to_ecef, enu_basis


def sun_unit_eci(jd: float) -> np.ndarray:
    """Approximate Sun direction unit vector in ECI (sufficient for illumination)."""
    n = jd - 2451545.0
    L = np.radians((280.460 + 0.9856474 * n) % 360.0)
    g = np.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = L + np.radians(1.915 * np.sin(g) + 0.020 * np.sin(2 * g))
    eps = np.radians(23.439 - 4.0e-7 * n)
    return np.array([
        np.cos(lam),
        np.cos(eps) * np.sin(lam),
        np.sin(eps) * np.sin(lam),
    ])


def apply_refraction(elevation_deg: float, pressure_hpa: float = 1013.25, temperature_c: float = 15.0) -> float:
    """Saemundsson refraction formula (returns apparent elevation in degrees)."""
    if elevation_deg < -1.0:
        return elevation_deg
    R = 1.02 / np.tan(np.radians(elevation_deg + 10.3 / (elevation_deg + 5.11)))
    R *= (pressure_hpa / 1010.0) * (283.0 / (273.0 + temperature_c))
    return elevation_deg + R / 60.0


def look_angles(
    r_sat_eci: np.ndarray,
    obs_lat: float,
    obs_lon: float,
    obs_alt: float,
    jd: float,
    theta0: float,
    apply_atm_refraction: bool = True,
):
    """Compute topocentric azimuth, elevation, range from observer to satellite.

    Returns
    -------
    az_deg, el_deg, range_m, el_apparent_deg
    """
    r_obs_ecef = geodetic_to_ecef(obs_lat, obs_lon, obs_alt)
    c, s = np.cos(theta0), np.sin(theta0)
    r_obs = np.array([
        c * r_obs_ecef[0] - s * r_obs_ecef[1],
        s * r_obs_ecef[0] + c * r_obs_ecef[1],
        r_obs_ecef[2],
    ])

    rho = r_sat_eci - r_obs
    range_m = float(np.linalg.norm(rho))
    if range_m < 1.0:
        return 0.0, 90.0, range_m, 90.0

    e, n, up = enu_basis(r_obs)
    east = float(np.dot(rho, e))
    north = float(np.dot(rho, n))
    up_comp = float(np.dot(rho, up))

    az = (np.degrees(np.arctan2(east, north)) + 360.0) % 360.0
    el = np.degrees(np.arcsin(np.clip(up_comp / range_m, -1.0, 1.0)))

    el_app = apply_refraction(el) if apply_atm_refraction else el
    return az, el, range_m, el_app


def is_illuminated(r_sat_eci: np.ndarray, jd: float, margin_km: float = 0.0) -> bool:
    """Simple geometric illumination test (Sun not occulted by Earth)."""
    sun = sun_unit_eci(jd)
    r = r_sat_eci
    rn = np.linalg.norm(r)
    cos_angle = -np.dot(r / rn, sun)
    sin_earth = (RE + margin_km * 1000.0) / rn
    if sin_earth >= 1.0:
        return False
    return cos_angle < np.sqrt(max(0.0, 1.0 - sin_earth ** 2))
