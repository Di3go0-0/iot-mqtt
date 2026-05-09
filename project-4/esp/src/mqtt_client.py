import ujson
import ubinascii
import machine
from umqtt.robust import MQTTClient
from machine import Pin
from crypto_utils import get_public_key, compute_shared_secret, encrypt, decrypt

led_d4 = Pin(4, Pin.OUT)
led_d4.off()

TOPIC_PUB_GET = "iot_pub_get"
TOPIC_SERVER = "iot_server_topic"
TOPIC_ESP = "iot_esp_topic"

server_aes_key = None


def conectar_mqtt(host="broker.hivemq.com", puerto=1883):
    cliente_id = ubinascii.hexlify(machine.unique_id())
    cliente = MQTTClient(cliente_id, host, puerto)
    try:
        cliente.connect()
        print("Conectado al broker MQTT:", host)
        return cliente
    except OSError as e:
        print("Error conectando a MQTT:", e)
        return None


def _on_pub_get(msg):
    global server_aes_key
    try:
        data = ujson.loads(msg)
        if "pub_send" in data:
            server_pub = data["pub_send"]
            server_aes_key = compute_shared_secret(server_pub)
            print("Llave del servidor recibida, shared secret establecido")
    except Exception as e:
        print("Error en key exchange:", e)


def _crear_callback(my_user):
    def _on_message(topic, msg):
        try:
            data = ujson.loads(msg)
            topic_str = topic.decode() if isinstance(topic, bytes) else topic

            if topic_str == TOPIC_PUB_GET:
                _on_pub_get(msg)
                return

            if topic_str != TOPIC_ESP:
                return

            if data.get("to") != my_user:
                return

            if not server_aes_key:
                print("No hay clave compartida aun")
                return

            plaintext = decrypt(
                data["ciphertext"], data["tag"], data["nonce"], server_aes_key
            )
            payload = ujson.loads(plaintext)
            print("Datos descifrados:", payload)

            action = data.get("action")
            if action == "led" and "state" in payload:
                status = payload["state"]
                if status == 0:
                    led_d4.on()
                    print("LED D4 ON")
                elif status == 1:
                    led_d4.off()
                    print("LED D4 OFF")

        except Exception as e:
            print("Error procesando mensaje:", e)

    return _on_message


def solicitar_llave(cliente, my_user):
    pub_key = get_public_key()
    payload = {"pub_get": pub_key, "user": my_user}
    cliente.publish(TOPIC_PUB_GET, ujson.dumps(payload))
    print("Llave publica enviada, esperando respuesta del servidor...")


def suscribirse(cliente, my_user):
    cliente.set_callback(_crear_callback(my_user))
    cliente.subscribe(TOPIC_PUB_GET)
    cliente.subscribe(TOPIC_ESP)
    print("Suscrito a:", TOPIC_PUB_GET, "y", TOPIC_ESP)


def publicar(cliente, action, data, my_user, to="server"):
    global server_aes_key
    if not server_aes_key:
        print("No se puede publicar: no hay clave compartida")
        return

    plaintext = dict(data)
    plaintext["user"] = my_user

    ciphertext, tag, nonce = encrypt(ujson.dumps(plaintext), server_aes_key)

    payload = {
        "pub": get_public_key(),
        "action": action,
        "to": to,
        "ciphertext": ciphertext,
        "tag": tag,
        "nonce": nonce,
    }
    cliente.publish(TOPIC_SERVER, ujson.dumps(payload))


def tiene_clave():
    return server_aes_key is not None
