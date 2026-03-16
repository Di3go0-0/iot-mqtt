import json
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8791517471:AAEfwJ5iJpTJfR72SggWSIg20Tfi1x-TBJU"

BROKER = "broker.hivemq.com"
# PORT 8884
TOPIC = "test0-0"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)


async def blink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Uso: /blink veces tiempo_ms")
        return

    times = int(context.args[0])
    delay = int(context.args[1])

    payload = {"times": times, "delay": delay}

    client.publish(TOPIC, json.dumps(payload))

    await update.message.reply_text(
        f"LED parpadeará {times} veces con delay {delay} ms"
    )


async def led_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client.publish(TOPIC, "1")
    await update.message.reply_text("LED ENCENDIDO")


async def led_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client.publish(TOPIC, "0")
    await update.message.reply_text("LED APAGADO")


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("blink", blink))
app.add_handler(CommandHandler("on", led_on))
app.add_handler(CommandHandler("off", led_off))

print("Bot corriendo...")

app.run_polling()
