import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";
import mqtt from "mqtt";
import path from "path";
import { Pool } from "pg";
import { initCrypto, encryptValue, decryptValue } from "./crypto";

const app = express();
const http = createServer(app);
const io = new Server(http);

const { publicKey: serverPublicKey, aesKey } = initCrypto();

// PostgreSQL
const pool = new Pool({
  host: "127.0.0.1",
  port: 5432,
  database: "iot",
  user: "admin",
  password: "admin123",
});

// MQTT
const mqttClient = mqtt.connect("mqtt://broker.hivemq.com:1883");

mqttClient.on("connect", () => {
  console.log("MQTT connected");
  mqttClient.subscribe("iottemp");
});

mqttClient.on("message", (_topic, message) => {
  try {
    const data = JSON.parse(message.toString());
    console.log(data)

    let temp = data.temp;
    let hum = data.hum;

    if (typeof temp === "string" && typeof hum === "string") {
      temp = Number(decryptValue(temp, aesKey));
      hum = Number(decryptValue(hum, aesKey));
    }

    io.emit("sensorData", { temp, hum });

    pool
      .query("INSERT INTO public.temp_hum (temp, hum) VALUES ($1, $2)", [
        String(temp),
        String(hum),
      ])
      .catch((err) => console.error("DB insert error:", err.message));
  } catch (err) {
    console.error("Parse error:", err);
  }
});

// Express config
app.set("view engine", "pug");
app.set("views", path.join(__dirname, "../views"));
app.use(express.static(path.join(__dirname, "../public")));
app.use(express.json());

// Routes
app.get("/", (_req, res) => {
  res.render("dashboard");
});

app.post("/api/led", (req, res) => {
  const { state } = req.body;
  const payload = {
    state: encryptValue(state, aesKey),
    user: "web-dashboard",
    to: "espGhoul",
    key: serverPublicKey,
  };

  mqttClient.publish("iotled", JSON.stringify(payload));

  // Log to PostgreSQL
  pool
    .query("INSERT INTO logs (user_name, action) VALUES ($1, $2)", [
      payload.user,
      String(state),
    ])
    .catch((err) => console.error("DB log error:", err.message));

  res.json({ ok: true });
});

// Socket.IO
io.on("connection", (socket) => {
  console.log("Client connected");
  socket.on("disconnect", () => console.log("Client disconnected"));
});

const PORT = 3000;
http.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
