import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8791517471:AAEfwJ5iJpTJfR72SggWSIg20Tfi1x-TBJU"

BROKER = "broker.hivemq.com"
# PORT 8884
TOPIC = "test0-0"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)


async def led_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client.publish(TOPIC, "1")
    await update.message.reply_text("LED ENCENDIDO")


async def led_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    client.publish(TOPIC, "0")
    await update.message.reply_text("LED APAGADO")


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("on", led_on))
app.add_handler(CommandHandler("off", led_off))

print("Bot corriendo...")

app.run_polling()
