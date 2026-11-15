"""ASTROCAM FastAPI application – high-accuracy rocket visibility predictor."""

from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import numpy as np

from engine.constants import D2R
from engine.coordinates import geodetic_to_ecef, gmst, enu_basis
from engine.visibility import look_angles, is_illuminated

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

app = FastAPI(
    title="ASTROCAM",
    version="0.1.0",
    description="High-accuracy rocket launch visibility & sky-pass predictor",
)

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


class ObserverInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Observer latitude (deg)")
    lon: float = Field(..., ge=-180, le=180, description="Observer longitude (deg)")
    alt_m: float = Field(default=0.0, ge=-500, le=9000, description="Observer altitude (m)")


class LaunchSiteInput(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    alt_m: float = Field(default=0.0, ge=-500, le=5000)
    name: str = Field(default="Launch Site")


class SimplePassRequest(BaseModel):
    """Minimal request for early testing of look-angle & illumination."""
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
    return {"message": "ASTROCAM API is running. Frontend not yet deployed.", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "ASTROCAM",
        "version": app.version,
        "features": ["look_angles", "refraction", "illumination", "foundation"],
    }


@app.post("/api/test_look")
def test_look(data: SimplePassRequest):
    """Quick geometric test: place a point along the launch azimuth and compute look angles."""
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
        data.observer.lat,
        data.observer.lon,
        data.observer.alt_m,
        jd,
        theta0,
        apply_atm_refraction=True,
    )

    illuminated = is_illuminated(r_test, jd)

    return {
        "azimuth_deg": round(az_deg, 3),
        "elevation_deg": round(el_deg, 3),
        "elevation_apparent_deg": round(el_app, 3),
        "range_km": round(rng / 1000.0, 2),
        "illuminated": illuminated,
        "note": "Geometric test point only – full ascent simulation coming next",
    }


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
