# ASTROCAM

**High-accuracy Rocket Launch Visibility & Sky-Pass Predictor**

Runs entirely in the browser (pure JavaScript). No server required.

## Live Demo

After enabling GitHub Pages (Settings → Pages → Deploy from branch `main` / root):

**https://meta43260-cyber.github.io/ASTROCAM/**

## Features

- 3DOF ascent dynamics + J2 gravity
- Multi-stage vehicles + fairing jettison
- US-1976 atmosphere + Mach-dependent drag
- Launch-azimuth locked inertial plane
- Atmospheric refraction (Saemundsson)
- Solar illumination check
- Observer look-angle timeline
- Interactive Leaflet ground track
- Fully client-side → works on GitHub Pages

## How to use

1. Set observer coordinates (default = Bangkok)
2. Set launch site + azimuth
3. Adjust stage parameters / payload if desired
4. Click **จำลองการมองเห็น**
5. View summary + map track

## Local development

Just open `index.html` with a local static server (modules require http):

```bash
npx serve .
# or
python -m http.server 8000
```

## Project structure

```
ASTROCAM/
├── index.html              ← entry point for GitHub Pages
├── js/engine/              ← high-accuracy physics (JS)
│   ├── constants.js
│   ├── atmosphere.js
│   ├── coordinates.js
│   ├── dynamics.js
│   ├── guidance.js
│   ├── vehicle.js
│   ├── ascent.js
│   └── visibility.js
├── static/
│   ├── app.js
│   └── style.css
└── (Python version still available for advanced server use)
```

## License

MIT
