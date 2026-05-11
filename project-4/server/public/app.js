const socket = io();
const MAX_POINTS = 30;
const DEVICES = ["espGhoul", "esp8a"];

function makeChart(canvasId, label, color) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label,
          data: [],
          borderColor: color,
          backgroundColor: color + "22",
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      animation: { duration: 300 },
      scales: {
        x: { ticks: { color: "#484f58", maxTicksLimit: 8 }, grid: { color: "#21262d" } },
        y: { ticks: { color: "#484f58" }, grid: { color: "#21262d" } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

const charts = {};
DEVICES.forEach((d) => {
  charts[d] = {
    temp: makeChart("tempChart-" + d, "Temp (°C)", "#f0883e"),
    hum: makeChart("humChart-" + d, "Hum (%)", "#58a6ff"),
  };
});

function addPoint(chart, label, value) {
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  if (chart.data.labels.length > MAX_POINTS) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update();
}

// Sensor data
socket.on("sensorData", (data) => {
  const dc = charts[data.source];
  if (!dc) return;
  const time = new Date().toLocaleTimeString();
  addPoint(dc.temp, time, data.temp);
  addPoint(dc.hum, time, data.hum);
  refreshReport(data.source);
});

// Device status
function setDeviceStatus(user, online) {
  const dot = document.getElementById("status-" + user);
  if (dot) dot.classList.toggle("online", online);
}

socket.on("devicesInit", (devices) => {
  for (const [user, online] of Object.entries(devices)) {
    setDeviceStatus(user, online);
  }
});

socket.on("deviceStatus", (data) => {
  setDeviceStatus(data.user, data.online);
});

// Tabs
function switchTab(device) {
  DEVICES.forEach((d) => {
    document.getElementById("tab-" + d).classList.toggle("active", d === device);
    document.getElementById("panel-" + d).classList.toggle("hidden", d !== device);
  });
}

// LED control
function sendLed(state, to) {
  fetch("/api/led", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state, to }),
  });
}

// Reports
function trendHtml(diff) {
  if (diff === null) return '<span class="trend-stable">—</span>';
  if (diff > 0.5) return `<span class="trend-up">↑ +${diff}</span>`;
  if (diff < -0.5) return `<span class="trend-down">↓ ${diff}</span>`;
  return '<span class="trend-stable">→ estable</span>';
}

function formatDate(iso) {
  return new Date(iso).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "medium" });
}

function renderReport(box, data) {
  if (data.empty) {
    box.innerHTML = '<p class="report-empty">Sin datos disponibles</p>';
    return;
  }

  const { last, stats, trend } = data;

  box.innerHTML = `
    <div class="report-header">
      <h4>Reporte en vivo</h4>
      <span class="report-time">${formatDate(last.time)}</span>
    </div>
    <div class="report-live">
      <div class="live-card">
        <div class="live-label">Temperatura</div>
        <div class="live-value temp">${last.temp}°C</div>
      </div>
      <div class="live-card">
        <div class="live-label">Humedad</div>
        <div class="live-value hum">${last.hum}%</div>
      </div>
    </div>
    <div class="report-stats">
      <div class="stat-group">
        <div class="stat-title">Temperatura (${stats.count} lecturas)</div>
        <div class="stat-row"><span class="stat-label">Promedio</span><span class="stat-val">${stats.temp.avg}°C</span></div>
        <div class="stat-row"><span class="stat-label">Min</span><span class="stat-val">${stats.temp.min}°C</span></div>
        <div class="stat-row"><span class="stat-label">Max</span><span class="stat-val">${stats.temp.max}°C</span></div>
        <div class="stat-row"><span class="stat-label">Tendencia</span><span class="stat-val">${trendHtml(trend.temp)}</span></div>
      </div>
      <div class="stat-group">
        <div class="stat-title">Humedad (${stats.count} lecturas)</div>
        <div class="stat-row"><span class="stat-label">Promedio</span><span class="stat-val">${stats.hum.avg}%</span></div>
        <div class="stat-row"><span class="stat-label">Min</span><span class="stat-val">${stats.hum.min}%</span></div>
        <div class="stat-row"><span class="stat-label">Max</span><span class="stat-val">${stats.hum.max}%</span></div>
        <div class="stat-row"><span class="stat-label">Tendencia</span><span class="stat-val">${trendHtml(trend.hum)}</span></div>
      </div>
    </div>
  `;
}

async function refreshReport(device) {
  const box = document.getElementById("report-" + device);
  if (!box) return;
  try {
    const res = await fetch("/api/reporte/" + device);
    const data = await res.json();
    renderReport(box, data);
  } catch {
    // silently skip on error
  }
}

// Load reports on init
DEVICES.forEach((d) => refreshReport(d));
