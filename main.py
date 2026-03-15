import network
import socket
import utime
from wifi_connection import connect
from machine import Pin
from mqtt_client import conectar_mqtt, publicar_mensaje_prueba, suscribirse

led = Pin(2, Pin.OUT)

print("Try in to connect...")


if connect("Diego", "1087546009"):
    led.on()
    print("Conectado al WiFi con éxito!")
    print("Try To connect to mqtt...")

    client = conectar_mqtt("broker.hivemq.com", 1883)

    if client:
        print("Conectado a HiveMQ!")
        # publicar_mensaje_prueba(client)
        suscribirse(client, "espeIoTUTP")
    else:
        print("Fallo en la conexión MQTT")
else:
    print("No se pudo conectar al WiFi. Revisa credenciales.")
