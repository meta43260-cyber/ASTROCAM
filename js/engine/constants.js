/** Physical and geodetic constants for ASTROCAM (SI units) */
export const MU = 3.986004418e14;
export const RE = 6378137.0;
export const FLAT = 1 / 298.257223563;
export const E2 = FLAT * (2 - FLAT);
export const OMEGA_E = 7.2921159e-5;
export const J2 = 1.08262668e-3;
export const G0 = 9.80665;
export const P0 = 101325.0;
export const R_AIR = 287.053;
export const GAMMA = 1.4;
export const Z_AXIS = [0, 0, 1];
export const D2R = Math.PI / 180;
export const R2D = 180 / Math.PI;
