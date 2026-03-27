from captive_portal import start_portal
from mqtt_client import conectar_mqtt, suscribirse, publicar
from button import fue_presionado
from wifi_connection import sta, led

while True:
    print("Lanzando portal de configuración WiFi...")
    start_portal()

    print("Conectando al broker MQTT...")
    client = conectar_mqtt("broker.hivemq.com", 1883)

    if not client:
        print("No se pudo conectar al broker MQTT")
        led.off()
        continue

    suscribirse(client, "8aPublicar")

    while sta.isconnected():
        client.check_msg()
        presionado, state = fue_presionado()
        if presionado:
            print("Botón state:", state)
            publicar(client, "8aRecibir", {"state": state})

    print("WiFi desconectado, relanzando portal...")
    led.off()
