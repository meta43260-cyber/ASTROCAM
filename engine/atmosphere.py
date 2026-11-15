"""US Standard Atmosphere 1976 (to ~86 km) + exponential extension."""

import numpy as np
from .constants import G0, R_AIR, GAMMA

# Layer table: (base geometric height m, base temperature K, lapse rate K/m, base pressure Pa)
_LAYERS = [
    (0.0,     288.15, -0.0065, 101325.0),
    (11000.0, 216.65,  0.0,     22632.10),
    (20000.0, 216.65,  0.0010,   5474.89),
    (32000.0, 228.65,  0.0028,    868.019),
    (47000.0, 270.65,  0.0,       110.906),
    (51000.0, 270.65, -0.0028,     66.9389),
    (71000.0, 214.65, -0.0020,      3.95642),
]

_H_TOP = 84852.0
_T_TOP = 186.946
_P_TOP = 0.37287
_HS = 6500.0  # scale height for exponential extension

# Simple Mach–Cd table for a typical launch vehicle
_MACH = np.array([0.0, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 5.0, 10.0, 25.0])
_CD   = np.array([0.30, 0.30, 0.34, 0.58, 0.62, 0.55, 0.45, 0.33, 0.28, 0.26, 0.25])


def atmosphere(h: float):
    """Return (density, pressure, temperature, speed_of_sound) at geometric height h (m)."""
    if h <= 0.0:
        h = 0.0
    if h >= _H_TOP:
        T = _T_TOP
        p = _P_TOP * np.exp(-(h - _H_TOP) / _HS)
    else:
        hb, Tb, L, pb = _LAYERS[0]
        for lay in _LAYERS:
            if h >= lay[0]:
                hb, Tb, L, pb = lay
            else:
                break
        if abs(L) < 1e-12:
            T = Tb
            p = pb * np.exp(-G0 * (h - hb) / (R_AIR * Tb))
        else:
            T = Tb + L * (h - hb)
            T = max(T, 1.0)
            p = pb * (T / Tb) ** (-G0 / (L * R_AIR))
    rho = p / (R_AIR * T)
    a = np.sqrt(GAMMA * R_AIR * T)
    return rho, p, T, a


def drag_coefficient(mach: float) -> float:
    """Interpolate drag coefficient from the internal Mach table."""
    return float(np.interp(mach, _MACH, _CD))
