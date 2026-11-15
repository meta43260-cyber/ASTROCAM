async function checkHealth() {
  const el = document.getElementById("health");
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    el.textContent = `สถานะ: ${data.status} | เวอร์ชัน ${data.version} | คุณสมบัติ: ${data.features.join(", ")}`;
  } catch (err) {
    el.textContent = "ไม่สามารถเชื่อมต่อ API ได้";
  }
}

document.getElementById("btn_test").addEventListener("click", async () => {
  const payload = {
    observer: {
      lat: parseFloat(document.getElementById("obs_lat").value),
      lon: parseFloat(document.getElementById("obs_lon").value),
      alt_m: 20,
    },
    launch_site: {
      lat: parseFloat(document.getElementById("site_lat").value),
      lon: parseFloat(document.getElementById("site_lon").value),
      alt_m: 10,
      name: "Test Site",
    },
    launch_azimuth_deg: parseFloat(document.getElementById("azimuth").value),
    launch_utc: new Date().toISOString(),
    test_altitude_km: parseFloat(document.getElementById("alt_km").value),
    test_downrange_km: parseFloat(document.getElementById("down_km").value),
  };

  const resultEl = document.getElementById("result");
  resultEl.textContent = "กำลังคำนวณ...";

  try {
    const res = await fetch("/api/test_look", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    resultEl.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    resultEl.textContent = "เกิดข้อผิดพลาด: " + err.message;
  }
});

checkHealth();
