async function checkHealth() {
  const el = document.getElementById("health");
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    el.textContent = `สถานะ: ${data.status} | เวอร์ชัน ${data.version} | ${data.features.join(", ")}`;
  } catch (err) {
    el.textContent = "ไม่สามารถเชื่อมต่อ API ได้";
  }
}

document.getElementById("btn_sim").addEventListener("click", async () => {
  const payload = {
    observer: {
      lat: parseFloat(document.getElementById("obs_lat").value),
      lon: parseFloat(document.getElementById("obs_lon").value),
      alt_m: 30,
    },
    launch_site: {
      lat: parseFloat(document.getElementById("site_lat").value),
      lon: parseFloat(document.getElementById("site_lon").value),
      alt_m: 10,
      name: "Launch Site",
    },
    launch_azimuth_deg: parseFloat(document.getElementById("azimuth").value),
    launch_utc: new Date().toISOString(),
    target_alt_km: parseFloat(document.getElementById("target_alt").value),
    stages: [
      {
        name: "Stage 1",
        thrust_sl_kN: parseFloat(document.getElementById("s1_thrust_sl").value),
        thrust_vac_kN: parseFloat(document.getElementById("s1_thrust_vac").value),
        isp_sl: parseFloat(document.getElementById("s1_isp_sl").value),
        isp_vac: parseFloat(document.getElementById("s1_isp_vac").value),
        prop_mass_kg: parseFloat(document.getElementById("s1_prop").value),
        dry_mass_kg: parseFloat(document.getElementById("s1_dry").value),
        burn_time_s: parseFloat(document.getElementById("s1_burn").value),
        area_m2: 22.0,
      },
      {
        name: "Stage 2",
        thrust_sl_kN: null,
        thrust_vac_kN: parseFloat(document.getElementById("s2_thrust_vac").value),
        isp_sl: null,
        isp_vac: parseFloat(document.getElementById("s2_isp_vac").value),
        prop_mass_kg: parseFloat(document.getElementById("s2_prop").value),
        dry_mass_kg: parseFloat(document.getElementById("s2_dry").value),
        burn_time_s: parseFloat(document.getElementById("s2_burn").value),
        area_m2: 10.0,
        ignition_delay_s: 5.0,
      },
    ],
    payload_kg: parseFloat(document.getElementById("payload").value),
    fairing_mass_kg: parseFloat(document.getElementById("fairing").value),
  };

  const resultEl = document.getElementById("result");
  resultEl.textContent = "กำลังจำลอง... (อาจใช้เวลาสักครู่)";

  try {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      resultEl.textContent = "Error: " + (data.detail || JSON.stringify(data));
      return;
    }

    const s = data.summary;
    let text = "=== สรุปผล ===\n";
    text += `เวลาสิ้นสุด powered flight: ${s.t_end_s} s\n`;
    text += `ความสูงสูงสุด: ${s.max_alt_km} km\n`;
    text += `มุมเงยสูงสุดที่มองเห็น: ${s.max_elevation_deg ?? "-"} °\n`;
    text += `จำนวนตัวอย่างที่มองเห็น (el > 5°): ${s.visible_samples}\n`;
    if (s.first_visible_t != null) {
      text += `เริ่มมองเห็นประมาณ T+${s.first_visible_t} s\n`;
      text += `สิ้นสุดการมองเห็นประมาณ T+${s.last_visible_t} s\n`;
    }
    text += "\n=== ตัวอย่างข้อมูล (บางส่วน) ===\n";
    text += JSON.stringify(data.samples.slice(0, 8), null, 2);
    if (data.samples.length > 8) {
      text += `\n... และอีก ${data.samples.length - 8} ตัวอย่าง`;
    }
    resultEl.textContent = text;
  } catch (err) {
    resultEl.textContent = "เกิดข้อผิดพลาด: " + err.message;
  }
});

checkHealth();
