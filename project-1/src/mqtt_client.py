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
        print("Mensaje recibido:", data)

        if "statusLed" in data:
            status = data["statusLed"]
            if status == 0:
                led_d4.on()
                print("LED D4 ON")
            elif status == 1:
                led_d4.off()
                print("LED D4 OFF")

        if "toggle" in data:
            if data["toggle"]:
                led_d4.value(not led_d4.value())
                print("LED D4 toggled:", "ON" if led_d4.value() else "OFF")

        if "state" in data:
            status = data["state"]
            if status == 0:
                led_d4.on()
                print("LED D4 ON")
            elif status == 1:
                led_d4.off()
                print("LED D4 OFF")

    except Exception as e:
        print("Error procesando mensaje:", e)


def suscribirse(cliente, topico="ghoulLed"):
    cliente.set_callback(_on_message)
    cliente.subscribe(topico)
    print("Suscrito a:", topico)


def publicar(cliente, topico, data):
    cliente.publish(topico, ujson.dumps(data))
