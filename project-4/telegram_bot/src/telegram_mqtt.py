import os
import json
import threading
import paho.mqtt.client as paho_mqtt
import psycopg2
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

# --- Roles y sesiones ---
ROLES = {
    "admin":     {"password": "1234", "devices": ["espGhoul", "esp8a"]},
    "diego":     {"password": "1234", "devices": ["espGhoul"]},
    "cristobal": {"password": "1234", "devices": ["esp8a"]},
}

# Sesiones activas: telegram_chat_id -> role_name
sessions: dict[int, str] = {}

# PostgreSQL
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "iot"),
    "user": os.environ.get("DB_USER", "admin"),
    "password": os.environ.get("DB_PASSWORD", "admin123"),
}

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


# --- Helpers ---
def get_user_devices(chat_id: int) -> list[str]:
    username = sessions.get(chat_id)
    if not username:
        return []
    return ROLES[username]["devices"]


def build_menu_for(chat_id: int):
    allowed = get_user_devices(chat_id)
    keyboard = []
    for dev in DEVICES:
        if dev["id"] in allowed:
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


LOGIN_MSG = "Inicia sesion con /login usuario contraseña"


# --- Telegram handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sessions:
        await update.message.reply_text(f"Control de LEDs IoT (MQTT cifrado)\n{LOGIN_MSG}")
        return
    await update.message.reply_text(
        "Selecciona un dispositivo:",
        reply_markup=build_menu_for(chat_id),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sessions:
        await update.message.reply_text(LOGIN_MSG)
        return
    await update.message.reply_text(
        "Selecciona un dispositivo:",
        reply_markup=build_menu_for(chat_id),
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args or len(args) != 2:
        await update.message.reply_text("Uso: /login usuario contraseña")
        return

    username, password = args[0].lower(), args[1]
    role = ROLES.get(username)

    if not role or role["password"] != password:
        await update.message.reply_text("Usuario o contraseña incorrectos.")
        return

    sessions[chat_id] = username
    devices_str = ", ".join(role["devices"])
    await update.message.reply_text(
        f"Bienvenido {username}. Acceso a: {devices_str}\nSelecciona un dispositivo:",
        reply_markup=build_menu_for(chat_id),
    )


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in sessions:
        del sessions[chat_id]
    await update.message.reply_text("Sesion cerrada.")


async def reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in sessions:
        await update.message.reply_text(LOGIN_MSG)
        return

    args = context.args
    if not args:
        allowed = get_user_devices(chat_id)
        await update.message.reply_text(
            f"Uso: /reporte <dispositivo>\nDisponibles: {', '.join(allowed)}"
        )
        return

    device = args[0]
    allowed = get_user_devices(chat_id)
    if device not in allowed:
        await update.message.reply_text("No tienes permiso para ese dispositivo.")
        return

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Ultima lectura
        cur.execute(
            "SELECT temp, hum, created_at FROM temp_hum WHERE source = %s ORDER BY created_at DESC LIMIT 1",
            (device,),
        )
        last = cur.fetchone()

        # Stats ultimas 50 lecturas
        cur.execute(
            """SELECT
                COUNT(*),
                ROUND(AVG(temp::numeric), 1),
                ROUND(MIN(temp::numeric), 1),
                ROUND(MAX(temp::numeric), 1),
                ROUND(AVG(hum::numeric), 1),
                ROUND(MIN(hum::numeric), 1),
                ROUND(MAX(hum::numeric), 1),
                MIN(created_at),
                MAX(created_at)
            FROM (
                SELECT temp, hum, created_at FROM temp_hum
                WHERE source = %s ORDER BY created_at DESC LIMIT 50
            ) sub""",
            (device,),
        )
        stats = cur.fetchone()

        # Tendencia: comparar promedio ultimas 10 vs anteriores 10
        cur.execute(
            """SELECT ROUND(AVG(temp::numeric), 1), ROUND(AVG(hum::numeric), 1)
            FROM (SELECT temp, hum FROM temp_hum WHERE source = %s ORDER BY created_at DESC LIMIT 10) sub""",
            (device,),
        )
        recent = cur.fetchone()

        cur.execute(
            """SELECT ROUND(AVG(temp::numeric), 1), ROUND(AVG(hum::numeric), 1)
            FROM (SELECT temp, hum FROM temp_hum WHERE source = %s ORDER BY created_at DESC LIMIT 10 OFFSET 10) sub""",
            (device,),
        )
        prev = cur.fetchone()

        cur.close()
        conn.close()
    except Exception as e:
        await update.message.reply_text(f"Error al consultar DB: {e}")
        return

    if not last:
        await update.message.reply_text(f"No hay datos para {device}.")
        return

    count, avg_t, min_t, max_t, avg_h, min_h, max_h, desde, hasta = stats
    last_t, last_h, last_ts = last

    def trend_icon(recent_val, prev_val):
        if prev_val is None or recent_val is None:
            return "—"
        diff = float(recent_val) - float(prev_val)
        if diff > 0.5:
            return f"↑ +{diff:.1f}"
        elif diff < -0.5:
            return f"↓ {diff:.1f}"
        return "→ estable"

    trend_t = trend_icon(recent[0], prev[0]) if prev[0] else "—"
    trend_h = trend_icon(recent[1], prev[1]) if prev[1] else "—"

    desde_str = desde.strftime("%d/%m %H:%M") if desde else "—"
    hasta_str = hasta.strftime("%d/%m %H:%M") if hasta else "—"
    last_str = last_ts.strftime("%d/%m/%Y %H:%M:%S")

    lines = [
        f"📊 *Reporte {device}*",
        "",
        f"🕐 Ultima lectura: {last_str}",
        f"   Temp: *{last_t}°C*  |  Hum: *{last_h}%*",
        "",
        f"📈 Resumen ({count} lecturas, {desde_str} — {hasta_str})",
        "",
        f"🌡 *Temperatura*",
        f"   Promedio: {avg_t}°C",
        f"   Min: {min_t}°C  |  Max: {max_t}°C",
        f"   Tendencia: {trend_t}",
        "",
        f"💧 *Humedad*",
        f"   Promedio: {avg_h}%",
        f"   Min: {min_h}%  |  Max: {max_h}%",
        f"   Tendencia: {trend_h}",
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    if chat_id not in sessions:
        await query.edit_message_text(text=LOGIN_MSG)
        return

    parts = query.data.split("|")
    if len(parts) != 3 or parts[0] != "led":
        return

    device = parts[1]
    action = parts[2]

    allowed = get_user_devices(chat_id)
    if device not in allowed:
        await query.edit_message_text(
            text="No tienes permiso para este dispositivo.",
            reply_markup=build_menu_for(chat_id),
        )
        return

    state = 0 if action == "on" else 1
    label = next((d["label"] for d in DEVICES if d["id"] == device), device)

    ok = send_led_command(device, state)

    status = "ENCENDIDO" if action == "on" else "APAGADO"
    if ok:
        text = f"{label} - LED {status}"
    else:
        text = "Error: no hay clave compartida con el servidor. Reinicia el bot."

    await query.edit_message_text(text=text, reply_markup=build_menu_for(chat_id))


async def post_init(application):
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Iniciar el bot"),
            BotCommand("login", "Iniciar sesion: /login usuario contraseña"),
            BotCommand("logout", "Cerrar sesion"),
            BotCommand("menu", "Menu de control de LEDs"),
            BotCommand("reporte", "Reporte temp/hum: /reporte dispositivo"),
        ]
    )


app = Application.builder().token(TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("login", login))
app.add_handler(CommandHandler("logout", logout))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("reporte", reporte))
app.add_handler(CallbackQueryHandler(button_callback))

print("Bot corriendo con MQTT cifrado...")
app.run_polling()
