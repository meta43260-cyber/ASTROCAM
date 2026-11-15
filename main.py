"""ASTROCAM FastAPI application – high-accuracy rocket visibility predictor."""

from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import numpy as np

from engine.constants import D2R, RE
from engine.coordinates import geodetic_to_ecef, gmst, enu_basis
from engine.visibility import look_angles, is_illuminated
from engine.vehicle import Stage, Vehicle
from engine.ascent import simulate_ascent

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(
    title="ASTROCAM",
    version="0.2.0",
    description="High-accuracy rocket launch visibility & sky-pass predictor",
)

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


class ObserverInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    alt_m: float = Field(default=20.0, ge=-500, le=9000)


class LaunchSiteInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    alt_m: float = Field(default=10.0, ge=-500, le=5000)
    name: str = Field(default="Launch Site")


class StageInput(BaseModel):
    name: str = "Stage"
    thrust_sl_kN: Optional[float] = Field(default=None, gt=0)
    thrust_vac_kN: float = Field(..., gt=0)
    isp_sl: Optional[float] = Field(default=None, gt=0)
    isp_vac: float = Field(..., gt=0)
    prop_mass_kg: float = Field(..., gt=0)
    dry_mass_kg: float = Field(..., ge=0)
    burn_time_s: float = Field(..., gt=0, le=2000)
    area_m2: float = Field(default=10.0, gt=0)
    ignition_delay_s: float = Field(default=0.0, ge=0)


class SimulateRequest(BaseModel):
    observer: ObserverInput
    launch_site: LaunchSiteInput
    launch_azimuth_deg: float = Field(..., ge=0, le=360)
    launch_utc: datetime
    target_alt_km: float = Field(default=400.0, ge=120, le=2000)
    stages: List[StageInput] = Field(..., min_length=1, max_length=5)
    payload_kg: float = Field(default=5000.0, ge=0)
    fairing_mass_kg: float = Field(default=1000.0, ge=0)
    vertical_time_s: float = Field(default=10.0, ge=0, le=30)
    kick_angle_deg: float = Field(default=7.0, ge=0, le=20)
    kick_duration_s: float = Field(default=14.0, ge=1, le=40)


class SimplePassRequest(BaseModel):
    observer: ObserverInput
    launch_site: LaunchSiteInput
    launch_azimuth_deg: float = Field(..., ge=0, le=360)
    launch_utc: datetime
    test_altitude_km: float = Field(default=200.0, ge=50, le=2000)
    test_downrange_km: float = Field(default=300.0, ge=0, le=5000)


@app.get("/")
def home():
    index = STATIC / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "ASTROCAM API is running", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "ASTROCAM",
        "version": app.version,
        "features": [
            "look_angles", "refraction", "illumination",
            "3dof_ascent", "multi_stage", "j2", "visibility_timeline"
        ],
    }


@app.post("/api/test_look")
def test_look(data: SimplePassRequest):
    jd = _jd_from_datetime(data.launch_utc)
    theta0 = gmst(jd)

    r_site_ecef = geodetic_to_ecef(
        data.launch_site.lat, data.launch_site.lon, data.launch_site.alt_m
    )
    c, s = np.cos(theta0), np.sin(theta0)
    r_site = np.array([
        c * r_site_ecef[0] - s * r_site_ecef[1],
        s * r_site_ecef[0] + c * r_site_ecef[1],
        r_site_ecef[2],
    ])

    e, n, up = enu_basis(r_site)
    az = data.launch_azimuth_deg * D2R
    horiz = np.sin(az) * e + np.cos(az) * n

    r_test = (
        r_site
        + horiz * (data.test_downrange_km * 1000.0)
        + up * (data.test_altitude_km * 1000.0)
    )

    az_deg, el_deg, rng, el_app = look_angles(
        r_test,
        data.observer.lat, data.observer.lon, data.observer.alt_m,
        jd, theta0, apply_atm_refraction=True,
    )
    illuminated = is_illuminated(r_test, jd)

    return {
        "azimuth_deg": round(az_deg, 3),
        "elevation_deg": round(el_deg, 3),
        "elevation_apparent_deg": round(el_app, 3),
        "range_km": round(rng / 1000.0, 2),
        "illuminated": illuminated,
    }


@app.post("/api/simulate")
def simulate(data: SimulateRequest):
    """Full multi-stage ascent + observer visibility timeline."""
    try:
        stages = []
        for s in data.stages:
            stages.append(Stage(
                name=s.name,
                thrust_sl=None if s.thrust_sl_kN is None else s.thrust_sl_kN * 1000.0,
                thrust_vac=s.thrust_vac_kN * 1000.0,
                isp_sl=s.isp_sl,
                isp_vac=s.isp_vac,
                prop_mass=s.prop_mass_kg,
                dry_mass=s.dry_mass_kg,
                burn_time=s.burn_time_s,
                area=s.area_m2,
                ignition_delay=s.ignition_delay_s,
            ))

        vehicle = Vehicle(
            stages=stages,
            payload=data.payload_kg,
            fairing_mass=data.fairing_mass_kg,
        )

        jd = _jd_from_datetime(data.launch_utc)

        df, final_state, t_end = simulate_ascent(
            vehicle=vehicle,
            site_lat=data.launch_site.lat,
            site_lon=data.launch_site.lon,
            site_alt=data.launch_site.alt_m,
            launch_azimuth_deg=data.launch_azimuth_deg,
            launch_jd=jd,
            target_alt=data.target_alt_km * 1000.0,
            vertical_time=data.vertical_time_s,
            kick_angle=data.kick_angle_deg,
            kick_duration=data.kick_duration_s,
            obs_lat=data.observer.lat,
            obs_lon=data.observer.lon,
            obs_alt=data.observer.alt_m,
        )

        if df.empty:
            raise HTTPException(500, "Simulation produced no samples")

        # Visibility summary
        visible = df[df["el_deg"].notna() & (df["el_deg"] > 5.0)]
        summary = {
            "t_end_s": round(t_end, 1),
            "max_alt_km": round(float(df["alt_km"].max()), 2),
            "max_elevation_deg": None if visible.empty else round(float(visible["el_deg"].max()), 2),
            "visible_samples": int(len(visible)),
            "first_visible_t": None if visible.empty else float(visible["t"].iloc[0]),
            "last_visible_t": None if visible.empty else float(visible["t"].iloc[-1]),
        }

        # Downsample for response size
        stride = max(1, len(df) // 400)
        samples = df.iloc[::stride].to_dict(orient="records")

        return {
            "summary": summary,
            "samples": samples,
            "note": "3DOF + J2 + refraction + illumination. Guidance is simplified; refine for operational use.",
        }
    except Exception as e:
        raise HTTPException(500, f"Simulation failed: {str(e)}")


def _jd_from_datetime(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    y, m = dt.year, dt.month
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    b = 2 - a + a // 4
    fraction = (dt.hour + dt.minute / 60 + dt.second / 3600 + dt.microsecond / 3.6e9) / 24
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + dt.day + b - 1524.5 + fraction
