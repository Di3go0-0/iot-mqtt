import os
import json
import threading
import paho.mqtt.client as paho_mqtt
from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from crypto_utils import get_public_key, compute_shared_secret, encrypt

TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "8791517471:AAEfwJ5iJpTJfR72SggWSIg20Tfi1x-TBJU"
)
BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883
BOT_USER = "telegramBot"

TOPIC_PUB_GET = "iot_pub_get"
TOPIC_SERVER = "iot_server_topic"

DEVICES = [
    {"id": "espGhoul", "label": "ESP Ghoul"},
    {"id": "esp8a", "label": "ESP 8a"},
]

# Estado global
server_aes_key = None
bot_public_key = get_public_key()
key_exchange_event = threading.Event()


# --- MQTT ---
def on_connect(client, userdata, flags, rc):
    print(f"MQTT conectado (rc={rc})")
    client.subscribe(TOPIC_PUB_GET)
    payload = {"pub_get": bot_public_key, "user": BOT_USER}
    client.publish(TOPIC_PUB_GET, json.dumps(payload))
    print("Key exchange enviado")


def on_message(client, userdata, msg):
    global server_aes_key
    try:
        data = json.loads(msg.payload.decode())
        if msg.topic == TOPIC_PUB_GET and "pub_send" in data:
            server_pub = data["pub_send"]
            server_aes_key = compute_shared_secret(server_pub)
            key_exchange_event.set()
            print("Key exchange completo")
    except Exception as e:
        print(f"Error MQTT: {e}")


mqtt_client = paho_mqtt.Client(client_id=f"telegram-bot-{os.getpid()}")
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
mqtt_client.loop_start()

print("Esperando key exchange...")
if not key_exchange_event.wait(timeout=15):
    print(
        "WARNING: Key exchange timeout, los comandos fallaran hasta que se establezca"
    )
else:
    print("Key exchange exitoso")


# --- LED command ---
def send_led_command(device: str, state: int) -> bool:
    if not server_aes_key:
        print("No hay clave compartida")
        return False

    plaintext = json.dumps({"state": state, "user": BOT_USER})
    ciphertext, tag, nonce = encrypt(plaintext, server_aes_key)

    payload = {
        "pub": bot_public_key,
        "action": "led",
        "to": device,
        "ciphertext": ciphertext,
        "tag": tag,
        "nonce": nonce,
    }
    mqtt_client.publish(TOPIC_SERVER, json.dumps(payload))
    return True


# --- Telegram ---
def build_main_menu():
    keyboard = []
    for dev in DEVICES:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{dev['label']} - ON", callback_data=f"led|{dev['id']}|on"
                ),
                InlineKeyboardButton(
                    f"{dev['label']} - OFF", callback_data=f"led|{dev['id']}|off"
                ),
            ]
        )
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Control de LEDs IoT (MQTT cifrado)\nSelecciona un dispositivo:",
        reply_markup=build_main_menu(),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selecciona un dispositivo:",
        reply_markup=build_main_menu(),
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|")
    if len(parts) != 3 or parts[0] != "led":
        return

    device = parts[1]
    action = parts[2]
    state = 0 if action == "on" else 1  # Activo bajo: 0=ON, 1=OFF
    label = next((d["label"] for d in DEVICES if d["id"] == device), device)

    ok = send_led_command(device, state)

    status = "ENCENDIDO" if action == "on" else "APAGADO"
    if ok:
        text = f"{label} - LED {status}"
    else:
        text = f"Error: no hay clave compartida con el servidor. Reinicia el bot."

    await query.edit_message_text(text=text, reply_markup=build_main_menu())


async def post_init(application):
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Iniciar el bot"),
            BotCommand("menu", "Mostrar menu de control de LEDs"),
        ]
    )


app = Application.builder().token(TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CallbackQueryHandler(button_callback))

print("Bot corriendo con MQTT cifrado...")
app.run_polling()
