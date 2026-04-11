# ESP32 - Quick Start Guide

## 1️⃣ Configurar Credenciales

```bash
nano esp32/config/settings.py
```

Editar:
```python
WIFI_SSID = "tu_red_wifi"
WIFI_PASSWORD = "tu_contraseña"
MQTT_BROKER = "broker.hivemq.com"  # o tu broker
MQTT_PORT = 1883
```

## 2️⃣ Transferir Archivos al ESP32

Usando `mpremote` (incluido en venv):

```bash
# Crear carpeta config en ESP32
mpremote mkdir :/config

# Copiar archivos
mpremote cp esp32/config/settings.py :/config/settings.py
mpremote cp esp32/src/wifi_connection.py :/wifi_connection.py
mpremote cp esp32/src/mqtt_client.py :/mqtt_client.py
mpremote cp esp32/src/main.py :/main.py
```

## 3️⃣ Ejecutar

Opción A - Serial interactivo:
```bash
mpremote
>>> import main
```

Opción B - Auto-start (crear boot.py en ESP32):
```python
# boot.py
import main
```

## 4️⃣ Ver Logs

```bash
mpremote monitor
```

Esperado:
```
[INIT] ESP32 Starting...
[INIT] Connecting to WiFi...
[WiFi] Connected: 192.168.1.100
[INIT] Connecting to MQTT...
[MQTT] Connected to broker.hivemq.com:1883
[MQTT] Subscribed to test0-0
[INIT] System ready!
```

## 5️⃣ Controlar LED Remotamente

Desde Telegram bot o publicar en MQTT:
```bash
mosquitto_pub -h broker.hivemq.com -t "test0-0" -m "1"  # LED ON
mosquitto_pub -h broker.hivemq.com -t "test0-0" -m "0"  # LED OFF
```

---

## API Disponible

### `wifi_connection.py`

```python
from wifi_connection import connect, disconnect, get_ip
from machine import Pin

# Conectar
led = Pin(2, Pin.OUT)
connect("SSID", "PASSWORD", led_pin=led)

# Obtener IP
ip = get_ip()
print(f"IP: {ip}")

# Desconectar
disconnect()
```

### `mqtt_client.py`

```python
from mqtt_client import conectar_mqtt, suscribirse, publicar

# Conectar
client = conectar_mqtt("broker.hivemq.com", 1883)

# Suscribirse
def on_message(topic, msg):
    print(f"Received: {msg.decode()}")

suscribirse(client, "test0-0", on_message)

# Publicar
publicar(client, "test0-0", "1")

# Loop (en main.py)
while True:
    client.check_msg()
```

---

## Troubleshooting

### WiFi no conecta
```
[WiFi] ERROR: SSID and password are required
```
✅ Verificar SSID y PASSWORD en settings.py

### MQTT no conecta
```
[MQTT] Connection error: [Errno 110] ETIMEDOUT
```
✅ Verificar broker y puerto
✅ Verificar WiFi conectada

### LED no responde
```
Enviar: mosquitto_pub -h broker.hivemq.com -t "test0-0" -m "1"
```
✅ Verificar MQTT_TOPIC_SUBSCRIBE en settings.py
✅ Verificar conexión MQTT

---

## Información Útil

**Broker de prueba gratuito:** broker.hivemq.com
**Puerto:** 1883 (sin SSL) o 8883 (con SSL)

**Monotorear topics:**
```bash
mosquitto_sub -h broker.hivemq.com -t "#"
```

**Pin LED por defecto:** GPIO 2
**Pin Botón por defecto:** GPIO 5

Cambiar en: `esp32/config/settings.py`

