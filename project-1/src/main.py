from captive_portal import start_portal
from mqtt_client import conectar_mqtt, suscribirse, publicar
from button import fue_presionado

print("Lanzando portal de configuración WiFi...")
start_portal()

print("Conectando al broker MQTT...")
client = conectar_mqtt("broker.hivemq.com", 1883)

if client:
    suscribirse(client, "ghoulLed")

    while True:
        client.check_msg()
        if fue_presionado():
            print("Botón presionado, enviando toggle a 8aled")
            publicar(client, "8aled", {"toggle": True})
            # publicar(client, "ghoulLed", {"toggle": True})
else:
    print("No se pudo conectar al broker MQTT")
