"""Vehicle and stage definitions for multi-stage ascent."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np
from .constants import P0, G0


@dataclass
class Stage:
    name: str
    thrust_sl: Optional[float]          # N (None for pure vacuum stages)
    thrust_vac: float                   # N
    isp_sl: Optional[float]             # s
    isp_vac: float                      # s
    prop_mass: float                    # kg
    dry_mass: float                     # kg
    burn_time: float                    # s
    area: float                         # m² reference area
    ignition_delay: float = 0.0         # s after previous stage sep
    burn_windows: Optional[List[Tuple[float, float]]] = None  # absolute T+ windows
    separation_t: Optional[float] = None
    thrust_curve: Optional[List[Tuple[float, float]]] = None  # (t, thrust_kN)

    def thrust(self, p: float, burn_elapsed: float = 0.0) -> float:
        f = min(max(p / P0, 0.0), 1.0)
        vacuum = self.thrust_vac
        if self.thrust_curve:
            times = [pt[0] for pt in self.thrust_curve]
            values = [pt[1] * 1000.0 for pt in self.thrust_curve]  # kN → N
            vacuum = float(np.interp(burn_elapsed, times, values))
        if self.thrust_sl is None:
            return vacuum
        if self.thrust_curve and self.thrust_vac > 0:
            return vacuum * (1.0 + (self.thrust_sl / self.thrust_vac - 1.0) * f)
        return vacuum + (self.thrust_sl - self.thrust_vac) * f

    def isp(self, p: float) -> float:
        if self.isp_sl is None:
            return self.isp_vac
        f = min(max(p / P0, 0.0), 1.0)
        return self.isp_vac + (self.isp_sl - self.isp_vac) * f


@dataclass
class Vehicle:
    stages: List[Stage]
    payload: float = 0.0
    fairing_mass: float = 0.0
    fairing_jettison_alt: float = 110000.0
    fairing_jettison_t: Optional[float] = None
    payload_deploy_t: Optional[float] = None

    def gross_mass(self) -> float:
        return (sum(s.prop_mass + s.dry_mass for s in self.stages)
                + self.payload + self.fairing_mass)
