# ASTROCAM

**High-accuracy Rocket Launch Visibility & Sky-Pass Predictor**

ASTROCAM predicts when and where a rocket will be visible in the sky from any observer location on Earth. It uses launch azimuth relative to the launch site, multi-stage vehicle timelines, and advanced orbital mechanics to produce low-error visibility forecasts.

## Key Features (Target)

- Observer location: manual coordinates or browser geolocation
- Multi-country / multi-launch-site support
- Launch azimuth-driven ground track and sky path
- Multi-stage vehicles + mission timeline (ignition, cutoff, separation, fairing, payload)
- 3-DOF ascent dynamics + J2 orbital propagation
- Atmospheric refraction correction for elevation angles
- Solar illumination / twilight photo-window estimation
- Azimuth–Elevation tracks, max elevation, pass duration
- Interactive map + sky polar plot
- Thai / English interface

## Physics Core

- Earth model: WGS84 + J2 perturbation
- Atmosphere: US-1976 layers + exponential upper atmosphere
- Drag: Mach-dependent Cd
- Coordinate frames: Geodetic ↔ ECEF ↔ ECI (GMST)
- Launch plane locked to requested Earth-fixed azimuth
- Closed-loop / energy-aware terminal guidance options
- Look-angle computation with optional refraction
- Solar position for illumination checks

## Project Structure

```
ASTROCAM/
├── README.md
├── requirements.txt
├── main.py                 # FastAPI application
├── engine/
│   ├── __init__.py
│   ├── constants.py
│   ├── atmosphere.py
│   ├── coordinates.py
│   ├── dynamics.py         # 3DOF + J2
│   ├── guidance.py
│   ├── visibility.py       # Look angles + refraction + illumination
│   └── vehicle.py
├── static/                 # Frontend assets
│   ├── index.html
│   ├── app.js
│   └── style.css
└── tests/
```

## Quick Start (local)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000

## Status

This repository is under active construction. The initial foundation includes the project layout and core physics modules. Full multi-stage simulation, refraction model, and polished web UI are being added incrementally.

## License

MIT
