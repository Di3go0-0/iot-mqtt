from captive_portal import start_portal
from mqtt_client import conectar_mqtt, suscribirse

print("Lanzando portal de configuración WiFi...")
start_portal()

print("Conectando al broker MQTT...")
client = conectar_mqtt("broker.hivemq.com", 1883)

if client:
    suscribirse(client, "ghoulLed")
else:
    print("No se pudo conectar al broker MQTT")
