import ujson
import time
from machine import Pin,
import ubinascii
from umqtt.robust import MQTTClient
import machine 

led = Pin(2, Pin.OUT)


def conectar_mqtt(host="test.mosquitto.org", puerto="1883"):
    cliente_id = ubinascii.hexlify(machine.unique_id())
    cliente = MQTTClient(cliente_id, host, puerto)
    try:
        cliente.connect()
        return cliente
    except OSError as e:
        print(f"Error conectando a MQTT: {e}")
        return False


def publicar_mensaje_prueba(cliente):
    topico = "espeIoTUTP"
    while True:
        cliente.publish(topico, "Its me")
        time.sleep(5)


def publicar_estado(cliente, topico_p, topico_s):
    cliente.set_callback(sub_cb)
    try:
        cliente.subscribe(topico_s)
        print("Suscrito manito")
    except:
        print("Error Manito")
    # topico = "SUTOPICO"
    boton = Pin(5, Pin.IN, Pin.PULL_UP)
    estado_actual = 5
    estado_pasado = 2
    while True:
        estado_actual = boton.value()
        if estado_actual != estado_pasado:
            cliente.publish(topico_p, str(boton.value()))
            estado_pasado = estado_actual
        cliente.check_msg()
        time.sleep_ms(10)


def sub_cb(topic, msg):
    led = Pin(2, Pin.OUT)
    if msg.decode() == "1":
        led.on()
    elif msg.decode() == "0":
        led.off()
    # led.toggle(msg.decode())
    print(topic, msg, msg.decode())


def sub_cb_json(topic, msg):
    try:
        data = ujson.loads(msg)

        times = data["times"]
        delay = data["delay"]

        print("Veces:", times)
        print("Delay:", delay)

        for i in range(times):
            led.on()
            time.sleep_ms(delay)

            led.off()
            time.sleep_ms(delay)

    except Exception as e:
        print("Error:", e)


def suscribirse(cliente, topico):
    cliente.set_callback(sub_cb_json)
    cliente.subscribe(topico)
    while True:
        cliente.check_msg()
