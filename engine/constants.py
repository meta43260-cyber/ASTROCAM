"""Physical and geodetic constants used throughout ASTROCAM."""

import numpy as np

# Gravitational parameter of Earth (m^3/s^2)
MU = 3.986004418e14

# WGS84 equatorial radius (m)
RE = 6378137.0

# WGS84 flattening
FLAT = 1.0 / 298.257223563
E2 = FLAT * (2.0 - FLAT)

# Earth rotation rate (rad/s)
OMEGA_E = 7.2921159e-5

# J2 zonal harmonic
J2 = 1.08262668e-3

# Standard gravity
G0 = 9.80665

# Sea-level standard pressure (Pa)
P0 = 101325.0

# Specific gas constant for dry air (J/(kg·K))
R_AIR = 287.053

# Ratio of specific heats
GAMMA = 1.4

# Unit vector along inertial Z-axis
Z_AXIS = np.array([0.0, 0.0, 1.0])

# Degree ↔ radian helpers
D2R = np.pi / 180.0
R2D = 180.0 / np.pi
