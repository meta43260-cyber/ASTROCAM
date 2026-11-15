import { Stage, Vehicle } from '../js/engine/vehicle.js';
import { simulateAscent } from '../js/engine/ascent.js';

// Julian Date from current time (UTC)
function jdNow() {
  const d = new Date();
  const y = d.getUTCFullYear(), m = d.getUTCMonth() + 1;
  let year = y, month = m;
  if (month <= 2) { year--; month += 12; }
  const A = Math.floor(year / 100);
  const B = 2 - A + Math.floor(A / 4);
  const fraction = (d.getUTCHours() + d.getUTCMinutes()/60 + d.getUTCSeconds()/3600) / 24;
  return Math.floor(365.25*(year+4716)) + Math.floor(30.6001*(month+1)) + d.getUTCDate() + B - 1524.5 + fraction;
}

let map, trackLine, markers = [];

function initMap() {
  map = L.map('map').setView([10, 20], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map);
}

document.getElementById('btn_sim').addEventListener('click', () => {
  const resultEl = document.getElementById('result');
  resultEl.textContent = 'กำลังจำลองในเบราว์เซอร์...';

  // Allow UI to update
  setTimeout(() => {
    try {
      const stages = [
        new Stage({
          name: 'Stage 1',
          thrustSl: parseFloat(document.getElementById('s1_tsl').value) * 1000,
          thrustVac: parseFloat(document.getElementById('s1_tvac').value) * 1000,
          ispSl: parseFloat(document.getElementById('s1_ispsl').value),
          ispVac: parseFloat(document.getElementById('s1_ispvac').value),
          propMass: parseFloat(document.getElementById('s1_prop').value),
          dryMass: parseFloat(document.getElementById('s1_dry').value),
          burnTime: parseFloat(document.getElementById('s1_burn').value),
          area: 22,
        }),
        new Stage({
          name: 'Stage 2',
          thrustSl: null,
          thrustVac: parseFloat(document.getElementById('s2_tvac').value) * 1000,
          ispSl: null,
          ispVac: parseFloat(document.getElementById('s2_ispvac').value),
          propMass: parseFloat(document.getElementById('s2_prop').value),
          dryMass: parseFloat(document.getElementById('s2_dry').value),
          burnTime: parseFloat(document.getElementById('s2_burn').value),
          area: 10,
          ignitionDelay: 5,
        }),
      ];

      const vehicle = new Vehicle({
        stages,
        payload: parseFloat(document.getElementById('payload').value),
        fairingMass: parseFloat(document.getElementById('fairing').value),
      });

      const obsLat = parseFloat(document.getElementById('obs_lat').value);
      const obsLon = parseFloat(document.getElementById('obs_lon').value);
      const siteLat = parseFloat(document.getElementById('site_lat').value);
      const siteLon = parseFloat(document.getElementById('site_lon').value);
      const az = parseFloat(document.getElementById('azimuth').value);
      const targetAlt = parseFloat(document.getElementById('target_alt').value) * 1000;

      const { samples, tEnd } = simulateAscent({
        vehicle,
        siteLat, siteLon, siteAlt: 10,
        launchAzimuthDeg: az,
        launchJd: jdNow(),
        targetAlt,
        obsLat, obsLon, obsAlt: 30,
        dt: 0.2,
        dtOut: 2.0,
      });

      // Summary
      const visible = samples.filter(s => s.el_deg != null && s.el_deg > 5);
      let text = '=== สรุปผล (Client-side) ===\n';
      text += `เวลาสิ้นสุด: ${tEnd.toFixed(1)} s\n`;
      text += `ความสูงสูงสุด: ${Math.max(...samples.map(s => s.alt_km)).toFixed(2)} km\n`;
      if (visible.length) {
        text += `มุมเงยสูงสุด: ${Math.max(...visible.map(s => s.el_deg)).toFixed(1)} °\n`;
        text += `เริ่มมองเห็น ~ T+${visible[0].t} s\n`;
        text += `สิ้นสุดการมองเห็น ~ T+${visible[visible.length-1].t} s\n`;
        text += `จำนวนจุดที่มองเห็น: ${visible.length}\n`;
      } else {
        text += 'ไม่พบช่วงที่มุมเงย > 5°\n';
      }
      text += '\nตัวอย่างข้อมูล:\n' + JSON.stringify(samples.slice(0, 6), null, 2);
      resultEl.textContent = text;

      // Update map
      if (trackLine) map.removeLayer(trackLine);
      markers.forEach(m => map.removeLayer(m));
      markers = [];

      const latlngs = samples.filter(s => s.lat && s.lon).map(s => [s.lat, s.lon]);
      if (latlngs.length) {
        trackLine = L.polyline(latlngs, { color: '#3d8bfd', weight: 3 }).addTo(map);
        map.fitBounds(trackLine.getBounds(), { padding: [30, 30] });

        // Observer marker
        markers.push(L.circleMarker([obsLat, obsLon], { radius: 7, color: '#0f0', fillColor: '#0f0', fillOpacity: 0.8 })
          .addTo(map).bindPopup('Observer'));
        // Launch site
        markers.push(L.circleMarker([siteLat, siteLon], { radius: 7, color: '#f80', fillColor: '#f80', fillOpacity: 0.8 })
          .addTo(map).bindPopup('Launch Site'));
      }
    } catch (err) {
      resultEl.textContent = 'เกิดข้อผิดพลาด: ' + err.message;
      console.error(err);
    }
  }, 50);
});

initMap();
