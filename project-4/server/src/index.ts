import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";
import mqtt from "mqtt";
import path from "path";
import { Pool } from "pg";
import { getPublicKey, computeSharedSecret, encrypt, decrypt } from "./crypto";

const app = express();
const http = createServer(app);
const io = new Server(http);

const serverPublicKey = getPublicKey();

// Diccionario de llaves: usuario -> aesKey
const clientKeys: Record<string, Buffer> = {};

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

const TOPIC_PUB_GET = "iot_pub_get";
const TOPIC_SERVER = "iot_server_topic";
const TOPIC_ESP = "iot_esp_topic";

mqttClient.on("connect", () => {
  console.log("MQTT connected");
  mqttClient.subscribe(TOPIC_PUB_GET);
  mqttClient.subscribe(TOPIC_SERVER);
});

mqttClient.on("message", (topic, message) => {
  try {
    const data = JSON.parse(message.toString());

    if (topic === TOPIC_PUB_GET) {
      handleKeyExchange(data);
      return;
    }

    if (topic === TOPIC_SERVER) {
      handleServerTopic(data);
      return;
    }
  } catch (err) {
    console.error("Parse error:", err);
  }
});

function handleKeyExchange(data: any) {
  if (!data.pub_get || !data.user) return;

  const espUser = data.user;
  const espPublicKey = data.pub_get;

  // Almacenar la llave compartida con este ESP
  clientKeys[espUser] = computeSharedSecret(espPublicKey);
  console.log(`Llave almacenada para: ${espUser}`);

  // Responder con la llave publica del servidor
  const response = {
    pub_send: serverPublicKey,
    user: "server",
  };
  mqttClient.publish(TOPIC_PUB_GET, JSON.stringify(response));
  console.log(`Llave publica enviada a: ${espUser}`);
}

function handleServerTopic(data: any) {
  const { pub, action, to, ciphertext, tag, nonce } = data;

  if (to !== "server") {
    // Reenviar a iot_esp_topic para que el ESP destino lo reciba
    mqttClient.publish(TOPIC_ESP, JSON.stringify(data));
    return;
  }

  // Buscar la aesKey del remitente por su llave publica
  const senderKey = findKeyByPub(pub);
  if (!senderKey) {
    console.error("No se encontro llave para pub:", pub);
    return;
  }

  const plaintext = decrypt(ciphertext, tag, nonce, senderKey.aesKey);
  const payload = JSON.parse(plaintext);
  console.log("Datos descifrados:", payload);

  if (action === "humtemp") {
    const temp = payload.temp;
    const hum = payload.hum;

    io.emit("sensorData", { temp, hum });

    pool
      .query("INSERT INTO public.temp_hum (temp, hum) VALUES ($1, $2)", [
        String(temp),
        String(hum),
      ])
      .catch((err) => console.error("DB insert error:", err.message));
  } else if (action === "led") {
    console.log(`LED action from ${payload.user}: state=${payload.state}`);
  }
}

function findKeyByPub(pub: number): { user: string; aesKey: Buffer } | null {
  for (const [user, aesKey] of Object.entries(clientKeys)) {
    // Recomputar la llave publica del ESP no es posible, pero podemos
    // computar el shared secret con la pub recibida y comparar
    const testKey = computeSharedSecret(pub);
    if (testKey.equals(aesKey)) {
      return { user, aesKey };
    }
  }
  // Si no se encuentra por comparacion, intentar computar directamente
  const aesKey = computeSharedSecret(pub);
  return { user: "unknown", aesKey };
}

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
  const { state, to = "espGhoul" } = req.body;

  const targetKey = clientKeys[to];
  if (!targetKey) {
    res.status(400).json({ error: `No key found for ${to}` });
    return;
  }

  const plaintext = JSON.stringify({ state, user: "server" });
  const { ciphertext, tag, nonce } = encrypt(plaintext, targetKey);

  const payload = {
    pub: serverPublicKey,
    action: "led",
    to,
    ciphertext,
    tag,
    nonce,
  };

  mqttClient.publish(TOPIC_ESP, JSON.stringify(payload));

  pool
    .query("INSERT INTO logs (user_name, action) VALUES ($1, $2)", [
      "server",
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
