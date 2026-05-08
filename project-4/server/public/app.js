const socket = io();

const MAX_POINTS = 30;

function makeChart(canvasId, label, color) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  return new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: label,
          data: [],
          borderColor: color,
          backgroundColor: color + "33",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { ticks: { color: "#aaa" }, grid: { color: "#333" } },
        y: { ticks: { color: "#aaa" }, grid: { color: "#333" } },
      },
      plugins: { legend: { labels: { color: "#eee" } } },
    },
  });
}

const tempChart = makeChart("tempChart", "Temp (C)", "#ff7f0e");
const humChart = makeChart("humChart", "Hum (%)", "#1f77b4");

function addPoint(chart, label, value) {
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  if (chart.data.labels.length > MAX_POINTS) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update();
}

socket.on("sensorData", (data) => {
  const time = new Date().toLocaleTimeString();
  addPoint(tempChart, time, data.temp);
  addPoint(humChart, time, data.hum);
});

function sendLed(state) {
  fetch("/api/led", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state }),
  });
}
