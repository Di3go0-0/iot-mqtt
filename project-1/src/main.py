from captive_portal import start_portal
from mqtt_client import conectar_mqtt, suscribirse, publicar
from button import fue_presionado

print("Lanzando portal de configuración WiFi...")
start_portal()

print("Conectando al broker MQTT...")
client = conectar_mqtt("broker.hivemq.com", 1883)

if client:
    suscribirse(client, "8aPublicar")

    while True:
        client.check_msg()
        presionado, state = fue_presionado()
        if presionado:
            print("Botón state:", state)
            publicar(client, "8aRecibir", {"state": state})
else:
    print("No se pudo conectar al broker MQTT")
