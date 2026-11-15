# ASTROCAM

**High-accuracy Rocket Launch Visibility & Sky-Pass Predictor**

ASTROCAM predicts when and where a rocket will be visible in the sky from any observer location on Earth. It uses launch azimuth relative to the launch site, multi-stage vehicle models, and advanced orbital mechanics.

## Current Features (v0.2)

- Observer location (manual coordinates)
- Multi-country / any launch site support
- Launch-azimuth locked inertial plane
- Multi-stage vehicles + fairing jettison
- 3-DOF ascent dynamics + J2 perturbation
- Atmospheric model (US-1976) + drag
- Atmospheric refraction correction (Saemundsson)
- Solar illumination check
- Full visibility timeline (azimuth, elevation, range)
- Simple web UI (Thai)

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

API docs: http://localhost:8000/docs

## API

- `GET /api/health`
- `POST /api/test_look` – geometric look-angle test
- `POST /api/simulate` – full multi-stage ascent + observer visibility

## Project Layout

```
ASTROCAM/
├── main.py
├── engine/
│   ├── constants.py
│   ├── atmosphere.py
│   ├── coordinates.py
│   ├── dynamics.py
│   ├── guidance.py
│   ├── vehicle.py
│   ├── ascent.py
│   └── visibility.py
├── static/
│   ├── index.html
│   ├── app.js
│   └── style.css
└── requirements.txt
```

## Roadmap

- Interactive Leaflet map + ground track
- Sky polar plot (azimuth-elevation path)
- Mission timeline editor (burn windows, separation)
- Better terminal guidance / energy management
- English / Thai language switch
- Preset vehicles (Falcon 9, Ariane 6, Electron…)
- Photo-window / twilight optimization

## License

MIT
