# Telegram Bot → MQTT → ESP32 LED Control

This project allows you to control an **ESP32 LED using Telegram**.  
The architecture connects a **Telegram Bot** to an **MQTT broker**, which sends commands to an **ESP32 running MicroPython**.

## Architecture

```
Telegram
   ↓
Telegram Bot
   ↓
Python Script (Bridge)
   ↓
MQTT Broker
   ↓
ESP32 (MicroPython)
   ↓
LED ON / OFF
```

The Telegram bot sends commands (`/on` and `/off`) that are published to an MQTT topic.  
The ESP32 subscribes to that topic and turns the LED **ON** or **OFF**.

---

# 1. Create a Telegram Bot

To create a Telegram bot you must use **BotFather**.

1. Open Telegram.
2. Search for **BotFather**.
3. Start the conversation.

```
/start
```

4. Create a new bot:

```
/newbot
```

5. Follow the instructions:
   - Choose a **bot name**
   - Choose a **username** (must end with `bot`)

Example:

```
Name: ESP LED Controller
Username: esp_led_controller_bot
```

6. BotFather will generate a **TOKEN**.

Example:

```
123456789:AAExampleTokenExampleTokenExample
```

Save this token. It will be used in your Python script.

---

# 2. Create a Python Virtual Environment

It is recommended to isolate dependencies.

```bash
python -m venv venv
source venv/bin/activate
```

---

# 3. Install Dependencies

Install the required libraries:

```bash
pip install python-telegram-bot paho-mqtt
```

Libraries used:

- **python-telegram-bot** → Telegram API communication
- **paho-mqtt** → MQTT communication

---

# 4. Create the Telegram–MQTT Bridge

Create a file called:

```
telegram_mqtt.py
```

Add the following code:

```python
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "YOUR_TELEGRAM_TOKEN"

BROKER = "broker.hivemq.com"
TOPIC = "espeIoTUTP"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)


async def led_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client.publish(TOPIC, "1")
    await update.message.reply_text("LED ON")


async def led_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client.publish(TOPIC, "0")
    await update.message.reply_text("LED OFF")


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("on", led_on))
app.add_handler(CommandHandler("off", led_off))

print("Telegram bot running...")

app.run_polling()
```

---

# 5. Run the Bot

Start the bot with:

```bash
python telegram_mqtt.py
```

You should see:

```
Telegram bot running...
```

---

# 6. Use the Bot in Telegram

Open Telegram and search for your bot.

Send commands:

### Turn LED ON

```
/on
```

The bot will publish:

```
1
```

to the MQTT topic.

---

### Turn LED OFF

```
/off
```

The bot will publish:

```
0
```

to the MQTT topic.

---

# 7. MQTT Configuration

Broker used:

```
broker.hivemq.com
```

Port:

```
1883
```

Topic example:

```
espeIoTUTP
```

The ESP32 must subscribe to this topic.

---

# 8. ESP32 Behavior

The ESP32 listens for MQTT messages:

| Message | Action |
|------|------|
| `1` | LED ON |
| `0` | LED OFF |

---

# 9. Security Recommendation

Public MQTT brokers can be used by anyone.

It is recommended to use a **unique topic**, for example:

```
utp/iot/juan/esp32/led
```

---

# 10. Future Improvements

Possible extensions:

- ESP32 sends LED status back to Telegram
- Control multiple devices
- Add sensors (temperature, humidity)
- Secure MQTT with authentication

---

# Author

IoT Project using:

- Telegram Bot
- MQTT
- ESP32
- MicroPython
