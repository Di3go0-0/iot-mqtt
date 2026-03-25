import ujson
import ubinascii
import machine
from umqtt.robust import MQTTClient
from machine import Pin

led_d4 = Pin(4, Pin.OUT)
led_d4.off()


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


def _on_message(topic, msg):
    try:
        data = ujson.loads(msg)
        status = data.get("statusLed", None)
        if status == 1:
            led_d4.on()
            print("LED D4 ON")
        elif status == 0:
            led_d4.off()
            print("LED D4 OFF")
    except Exception as e:
        print("Error procesando mensaje:", e)


def suscribirse(cliente, topico="ghoulLed"):
    cliente.set_callback(_on_message)
    cliente.subscribe(topico)
    print("Suscrito a:", topico)
    while True:
        cliente.check_msg()
